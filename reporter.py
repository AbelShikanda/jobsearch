# reporter.py
"""
Local Kenya organization report.

Groups results by organization and attaches a BI recommendation
to each org (instead of a cover letter).

Writes to two locations every run:
  reports/kenya_orgs_YYYY-MM-DD_HHMM.txt
  reports/archive/kenya_orgs_YYYY-MM-DD_HHMM.txt
"""
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import config
from models import Job


REPORTS_DIR = Path("reports")
ARCHIVE_DIR = REPORTS_DIR / "archive"


# ── Build the report as plain text ──────────────────────────
def build_text_report(jobs: list[Job]) -> str:
    by_org: dict[str, list[Job]] = defaultdict(list)
    for j in jobs:
        by_org[j.company or j.source or "Unknown"].append(j)

    lines: list[str] = []
    lines.append(
        f"🇰🇪 Local Kenya Organization Report — "
        f"{len(by_org)} orgs, {len(jobs)} roles"
    )
    lines.append(f"Region: {config.LOCAL_REGION}, {config.LOCAL_COUNTRY}")
    lines.append(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    lines.append("=" * 72)
    lines.append("")

    for org in sorted(by_org):
        items = by_org[org]
        lines.append(f"🏢 {org}")
        lines.append(f"   Location: {items[0].location or '—'}")
        lines.append(f"   Roles ({len(items)}):")
        for j in items:
            lines.append(f"     • {j.title}  — score {j.score}")
            lines.append(f"       Apply: {j.apply_url or j.url}")
            if j.email:
                lines.append(f"       Email: {j.email}")
            if j.reasons:
                lines.append(f"       Why:   {'; '.join(j.reasons[:5])}")
        lines.append("")

        rec = next(
            (getattr(j, "bi_recommendation", "") for j in items
             if getattr(j, "bi_recommendation", "")),
            "",
        )
        if rec:
            lines.append("   ── BI Improvement Recommendation ──")
            for line in rec.splitlines():
                lines.append(f"   {line}")
            lines.append("")

        lines.append("─" * 72)
        lines.append("")

    return "\n".join(lines)


# ── Write to both locations ─────────────────────────────────
def write_report_to_files(jobs: list[Job]) -> tuple[Path, Path]:
    REPORTS_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    content = build_text_report(jobs)

    primary = REPORTS_DIR / f"kenya_orgs_{stamp}.txt"
    archive = ARCHIVE_DIR / f"kenya_orgs_{stamp}.txt"

    primary.write_text(content, encoding="utf-8")
    archive.write_text(content, encoding="utf-8")

    print(f"[report] 💾 Wrote {primary}")
    print(f"[report] 💾 Wrote {archive}")
    return primary, archive


# ── Public entry point ──────────────────────────────────────
def send_report(jobs: list[Job]) -> None:
    if not jobs:
        print("[report] no local orgs — skipping")
        return
    write_report_to_files(jobs)