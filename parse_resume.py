"""
Reads resume.pdf (or .docx / .txt) and produces resume_profile.json.
Safe to run repeatedly — only rewrites when content changes.
"""
import json
import re
from pathlib import Path

DEFAULT_RESUME = "resume.pdf"
DEFAULT_OUTPUT = "resume_profile.json"

KNOWN_SKILLS = [
    # Languages
    "python", "javascript", "typescript", "php", "java", "go", "rust", "sql",
    "html", "css", "bash",
    # Frameworks
    "django", "flask", "fastapi", "laravel", "react", "vue", "node",
    "express", "next.js", "svelte",
    # Automation / scraping
    "playwright", "selenium", "puppeteer", "scrapy", "beautifulsoup",
    "requests", "httpx", "automation", "scraping", "crawling",
    "airflow", "n8n", "zapier",
    # Data / infra
    "postgresql", "mysql", "sqlite", "mongodb", "redis",
    "docker", "kubernetes", "aws", "gcp", "azure", "linux",
    "terraform", "nginx", "celery", "rabbitmq", "kafka",
    # Tools
    "git", "github", "gitlab", "ci/cd", "jira",
    # Domain
    "api", "rest", "graphql", "webhooks", "m-pesa", "payments",
    "stripe", "paypal", "sms", "whatsapp",
]

TITLE_PATTERNS = [
    r"(senior|junior|lead|principal|staff)?\s*(python|backend|full[- ]?stack|automation|scraping|software|data)\s*(developer|engineer|dev|architect)",
    r"freelance\s+(developer|engineer)",
    r"(software|backend|automation)\s+engineer",
]

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
YEARS_RE = re.compile(r"(\d+)\+?\s*years?", re.I)
NUM_HIGHLIGHT_RE = re.compile(
    r"(\d+%|\$\d+|\d+\s*(?:users|clients|projects|requests|hours|orders|records))",
    re.I,
)


# ── Extraction ──────────────────────────────────────────────
def extract_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Resume not found: {path}")

    if p.suffix.lower() == ".pdf":
        import pdfplumber
        parts = []
        with pdfplumber.open(p) as pdf:
            for page in pdf.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts)

    if p.suffix.lower() == ".docx":
        from docx import Document
        return "\n".join(para.text for para in Document(p).paragraphs)

    return p.read_text(encoding="utf-8", errors="ignore")


def extract_skills(text: str) -> list[str]:
    t = text.lower()
    return sorted({s for s in KNOWN_SKILLS if s in t})


def extract_titles(text: str) -> list[str]:
    found = []
    for pat in TITLE_PATTERNS:
        for m in re.finditer(pat, text, re.I):
            found.append(" ".join(m.group(0).split()).lower())
    return sorted(set(found))


def extract_years(text: str) -> int:
    matches = [int(m.group(1)) for m in YEARS_RE.finditer(text)]
    return max(matches) if matches else 0


def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text)
    return m.group(0) if m else ""


def extract_name(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if (
            2 <= len(line) <= 50
            and not any(c.isdigit() for c in line)
            and "@" not in line
            and not line.lower().startswith(("cv", "resume", "curriculum"))
        ):
            return line
    return ""


def extract_summary(text: str) -> str:
    m = re.search(
        r"(summary|profile|about)\s*[:\n]+(.{50,600})",
        text,
        re.I | re.S,
    )
    if m:
        return " ".join(m.group(2).split())
    return " ".join(text[:500].split())


def extract_highlights(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip("•-* \t")
        if NUM_HIGHLIGHT_RE.search(line) and 20 <= len(line) <= 200:
            lines.append(line)
    return lines[:8]


# ── Build & persist ─────────────────────────────────────────
def build_profile(resume_path: str) -> dict:
    text = extract_text(resume_path)
    return {
        "name":       extract_name(text),
        "email":      extract_email(text),
        "years":      extract_years(text),
        "titles":     extract_titles(text),
        "skills":     extract_skills(text),
        "summary":    extract_summary(text),
        "highlights": extract_highlights(text),
        "raw_text":   text,
    }


def save_profile(profile: dict, output_path: str = DEFAULT_OUTPUT) -> None:
    Path(output_path).write_text(
        json.dumps(profile, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def needs_reparse(
    resume_path: str = DEFAULT_RESUME,
    output_path: str = DEFAULT_OUTPUT,
) -> bool:
    r = Path(resume_path)
    o = Path(output_path)
    if not o.exists():
        return True
    if not r.exists():
        return False
    return r.stat().st_mtime > o.stat().st_mtime


def refresh_profile(
    resume_path: str = DEFAULT_RESUME,
    output_path: str = DEFAULT_OUTPUT,
    force: bool = False,
) -> dict:
    if not force and not needs_reparse(resume_path, output_path):
        return json.loads(Path(output_path).read_text(encoding="utf-8"))
    profile = build_profile(resume_path)
    save_profile(profile, output_path)
    return profile


if __name__ == "__main__":
    p = refresh_profile(force=True)
    print("✅ Wrote resume_profile.json")
    print(f"   Name:     {p['name']}")
    print(f"   Years:    {p['years']}")
    print(f"   Titles:   {', '.join(p['titles'][:3])}")
    print(f"   Skills:   {', '.join(p['skills'][:15])}")
    print(f"   Email:    {p['email']}")