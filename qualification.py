import re
from datetime import datetime, timezone
import config
from models import Job


SALARY_RE = re.compile(
    r"\$?\s*(\d{1,3}(?:[,\.]\d{3})*|\d+)\s*"
    r"(k|usd|/mo|/month|per month|/year|per year|annual)?",
    re.I,
)


def parse_salary_usd_monthly(text: str) -> int:
    if not text:
        return 0
    t = text.lower().replace(",", "")
    m = SALARY_RE.search(t)
    if not m:
        return 0
    try:
        num = float(m.group(1))
    except (TypeError, ValueError):
        return 0
    unit = (m.group(2) or "").lower()

    if "k" in unit or num < 500:
        num *= 1000
    if "/year" in t or "per year" in t or "annual" in t:
        num /= 12
    return int(num)


def _days_old(iso: str) -> int:
    if not iso:
        return 0
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return 0


def _reject(job: Job, reason: str) -> Job:
    job.score = -999
    job.reasons = [f"REJECTED: {reason}"]
    return job


# ── Kenya-only location gate ────────────────────────────────
def _is_local_kenya(job: Job) -> bool:
    loc = (job.location or "").lower()
    if not loc:
        return False
    if any(bad in loc for bad in config.REMOTE_BLACKLIST):
        return False
    return any(t in loc for t in config.LOCAL_TARGETS)


def score(job: Job) -> Job:
    text = f"{job.title} {job.description} {job.location}".lower()
    title_l = job.title.lower()
    company_l = (job.company or "").lower()
    url_l = (job.url or "").lower()
    apply_l = (job.apply_url or "").lower()
    s, reasons = 0, []

    # ── 0. KENYA LOCAL GATE — hard reject ───────────────────
    if not _is_local_kenya(job):
        loc = (job.location or "unknown").lower()
        if any(b in loc for b in config.REMOTE_BLACKLIST):
            return _reject(job, f"remote/online '{job.location}'")
        return _reject(job, f"not Kenyan local '{job.location or 'unknown'}'")

    # ── 0-ORG. Organization leads from Bright Data Maps ─────
    # These aren't job listings — they're local businesses to
    # approach with a BI pitch. Give them a baseline score so
    # they survive to the report and get a BI memo.
    if job.source == "brightdata_maps":
        job.score = 60
        job.reasons = ["+ local organization lead (BI pitch target)"]
        return job

    # ── 0a. Reject HN "chatty" titles ───────────────────────
    if len(job.title) > 90 or job.title.count(" ") > 15:
        return _reject(job, "title too long (likely HN comment)")
    if any(frag in title_l for frag in
           ["hiring:", "i'm working with", "looking for", "we're hiring for"]):
        return _reject(job, "recruiter post")

    # ── 0b. TITLE BLACKLIST ─────────────────────────────────
    for bad in config.TITLE_BLACKLIST:
        if bad in title_l:
            return _reject(job, f"title blacklist '{bad}'")

    # ── 0c. COMPANY BLACKLIST ───────────────────────────────
    for bad in config.COMPANY_BLACKLIST:
        if bad in company_l:
            return _reject(job, f"company blacklist '{bad}'")

    # ── 0d. URL BLACKLIST ───────────────────────────────────
    for bad in config.URL_BLACKLIST:
        if bad in url_l or bad in apply_l:
            return _reject(job, f"url blacklist '{bad}'")

    # ── 1. HARD REJECT keywords in title+description ────────
    for bad in config.HARD_REJECT:
        if bad in text:
            return _reject(job, f"hard reject '{bad}'")

    # ── 2. STRONG SKILL GATE ────────────────────────────────
    strong_matches = [sk for sk in config.STRONG_SKILLS if sk in text]
    if not strong_matches:
        return _reject(job, "no strong skill match")

    s += len(strong_matches) * config.STRONG_SKILL_WEIGHT
    reasons.extend(f"+ {sk}" for sk in strong_matches)

    # ── 3. MEDIUM SKILLS (bonus) ────────────────────────────
    for kw in config.MEDIUM_SKILLS:
        if kw in text and kw not in strong_matches:
            s += config.MEDIUM_SKILL_WEIGHT
            reasons.append(f"+ {kw}")

    # ── 4. TITLE MATCH ──────────────────────────────────────
    title_phrases = [
        "full stack", "fullstack", "full-stack",
        "software developer", "software engineer",
        "python developer", "python engineer",
        "backend developer", "backend engineer",
        "django developer",
        "laravel developer",
        "web developer", "web engineer",
        "automation developer", "automation engineer",
        "scraping developer", "scraping engineer",
        "javascript developer",
        "react developer", "react engineer",
        "data analyst", "business intelligence",
    ]
    if any(p in title_l for p in title_phrases):
        s += config.TITLE_MATCH_WEIGHT
        reasons.append("+ title match")

    # ── 5. LOCATION FIT (already Kenyan; small bonus) ───────
    if any(loc in (job.location or "").lower()
           for loc in config.LOCAL_TARGETS):
        s += config.LOCATION_WEIGHT
        reasons.append("+ location fit (Kenya)")

    # ── 6. SALARY ───────────────────────────────────────────
    sal = parse_salary_usd_monthly(job.salary or job.description)
    if sal >= config.MIN_SALARY_USD:
        s += config.SALARY_WEIGHT
        reasons.append(f"+ salary ~${sal}/mo")

    # ── 7. FRESHNESS ────────────────────────────────────────
    days = _days_old(job.posted_at)
    if days == 0:
        s += config.RECENT_WEIGHT
        reasons.append("+ fresh/undated")
    elif days <= 2:
        s += config.FRESH_WEIGHT
        reasons.append("+ very fresh")
    elif days <= 7:
        s += config.RECENT_WEIGHT
        reasons.append("+ recent")
    elif days > 30:
        s -= 10
        reasons.append("- stale")

    # ── 8. NICE TO HAVE ─────────────────────────────────────
    for kw in config.NICE_TO_HAVE:
        if kw in text:
            s += 2
            reasons.append(f"+ {kw}")

    # ── 9. DIRECT EMAIL ─────────────────────────────────────
    if job.email:
        s += config.EMAIL_WEIGHT
        reasons.append("+ direct email")

    job.score = s
    job.reasons = reasons
    return job


def qualifies(job: Job) -> bool:
    return job.score >= config.QUALIFY_THRESHOLD