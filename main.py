import asyncio
import sys
from urllib.parse import urlparse

import config
import refresh
from parse_resume import refresh_profile

from collectors.brightdata_maps import BrightDataMapsCollector
from collectors.serper          import SerperCollector
from collectors.config_driven   import ConfigDrivenCollector

from sites import SITES

from dedupe        import dedupe
from qualification import score, qualifies
from storage       import init_db, load_seen_fingerprints, save_jobs
from bi_advisor    import write_bi_recommendation
from reporter      import send_report

from playwright.async_api import async_playwright


API_COLLECTORS = [
    BrightDataMapsCollector,
    SerperCollector,
]


KENYAN_SITE_KEYWORDS = (
    "co.ke", "brightermonday", "fuzu", "myjobmag",
    "careers.ke", "kenya",
)

KENYAN_SITES = [
    s for s in SITES
    if any(kw in s["url"].lower() for kw in KENYAN_SITE_KEYWORDS)
]


# Sources that are NOT real organization names — skip BI memos
ANONYMOUS_SOURCES = {
    "serper",
    "config_driven",
    "brightdata_maps",
    "",
}


def is_kenyan_local(job) -> bool:
    loc = (getattr(job, "location", "") or "").lower()
    if not loc:
        return False
    if any(bad in loc for bad in config.REMOTE_BLACKLIST):
        return False
    return any(t in loc for t in config.LOCAL_TARGETS)


def _should_get_bi_memo(org: str) -> bool:
    """
    Only real, named organizations get a BI memo.
    Anonymous sources (job boards with no company) are skipped.
    """
    if not org:
        return False
    if org.strip().lower() in ANONYMOUS_SOURCES:
        return False
    if len(org) < 3 or len(org) > 80:
        return False
    return True


def _canonical_domain(url: str) -> str:
    """Return the bare domain for a URL, or '' if unparseable."""
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


async def run(force_resume: bool = False, dry_run: bool = False) -> None:
    refresh_profile(force=force_resume)
    cfg = refresh.reload_config()
    print(
        f"✅ Profile: {cfg.PROFILE['name']} "
        f"({cfg.PROFILE['years']} yrs, "
        f"{len(cfg.PROFILE['skills'])} skills)"
    )
    print(f"🇰🇪 Targeting: {cfg.LOCAL_REGION}, {cfg.LOCAL_COUNTRY}")

    # ── STAGE 1a: sync org collectors ───────────────────────
    api_jobs = []
    for C in API_COLLECTORS:
        try:
            fetched = C().fetch()
            print(f"[{C.name}] {len(fetched)} raw results")
            api_jobs.extend(fetched)
        except Exception as e:
            print(f"[{C.__name__}] crashed: {e}")

    # ── STAGE 1b: Kenyan job boards ─────────────────────────
    pw_jobs = []
    if KENYAN_SITES:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=cfg.HEADLESS)
            for site in KENYAN_SITES:
                try:
                    got = await ConfigDrivenCollector(site).fetch(
                        browser=browser
                    )
                    print(f"[{site['name']}] {len(got)} results")
                    pw_jobs.extend(got)
                except Exception as e:
                    print(f"[{site['name']}] crashed: {e}")
                await asyncio.sleep(6)
            await browser.close()
    else:
        print("⚠️  No Kenyan sites configured in sites.py")

    all_jobs = api_jobs + pw_jobs
    print(f"📥 Fetched {len(all_jobs)} raw local-Kenya results")

    if not all_jobs:
        print("⚠️  Nothing found. Check BrightData + site URLs.")
        return

    # ── STAGE 2: dedupe ─────────────────────────────────────
    init_db()
    seen = load_seen_fingerprints()
    fresh = dedupe(all_jobs, seen)
    print(f"🧹 {len(fresh)} new after dedupe")

    # ── STAGE 3: hard Kenya filter ──────────────────────────
    local = [j for j in fresh if is_kenyan_local(j)]
    print(f"🇰🇪 {len(local)} confirmed Kenyan & on-site")

    if not local:
        print("⚠️  No local Kenyan organizations matched.")
        return

    # ── STAGE 4: score & qualify ────────────────────────────
    scored    = [score(j) for j in local]
    qualified = [j for j in scored if qualifies(j)]
    print(f"⭐ {len(qualified)} qualified "
          f"(threshold {cfg.QUALIFY_THRESHOLD})")

    if not qualified:
        print("⚠️  No qualified results.")
        return

    # ── STAGE 5a: group by company name ─────────────────────
    # Only BrightData-discovered orgs get BI memos.
    # Job board listings (Serper, config_driven) are jobs, not
    # organizations — they stay in the report without a memo.
    raw_by_org: dict[str, list] = {}
    for job in qualified:
        if job.source != "brightdata_maps":
            job.bi_recommendation = ""
            continue
        key = (job.company or "").strip()
        if not key:
            continue
        raw_by_org.setdefault(key, []).append(job)

    # ── STAGE 5b: collapse orgs that share a domain ─────────
    seen_domains: dict[str, str] = {}
    by_org: dict[str, list] = {}

    for org, jobs in raw_by_org.items():
        domain = _canonical_domain(jobs[0].url or "")
        if domain and domain in seen_domains:
            canonical = seen_domains[domain]
            by_org.setdefault(canonical, []).extend(jobs)
        else:
            if domain:
                seen_domains[domain] = org
            by_org.setdefault(org, []).extend(jobs)

    # ── STAGE 5c: generate BI memos ─────────────────────────
    written = 0
    skipped = 0

    for org, jobs in by_org.items():
        if not _should_get_bi_memo(org):
            for j in jobs:
                j.bi_recommendation = ""
            skipped += 1
            continue

        try:
            rec = write_bi_recommendation(org, jobs)
            for j in jobs:
                j.bi_recommendation = rec
            print(f"📊 BI rec written: {org}")
            written += 1
        except Exception as e:
            print(f"[BI] failed for {org}: {e}")
            skipped += 1

    print(f"📊 BI memos: {written} written, {skipped} skipped")

    # ── STAGE 6: persist ────────────────────────────────────
    if not dry_run:
        save_jobs(local)
        print(f"💾 Saved {len(local)} to {cfg.DB_PATH}")
    else:
        print("🧪 dry-run: not saved, not reported")

    # ── STAGE 7: report ─────────────────────────────────────
    if not dry_run:
        send_report(qualified)


if __name__ == "__main__":
    asyncio.run(run(
        force_resume="--force-resume" in sys.argv,
        dry_run="--dry-run" in sys.argv,
    ))