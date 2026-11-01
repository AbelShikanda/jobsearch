# search_web.py
"""
Open Google Jobs searches in your default browser.

Not part of the automated pipeline. Run manually:
    py search_web.py

Each query uses Google's Jobs widget (ibp=htl;jobs) plus search
operators that narrow to recent, relevant, applicable roles.
"""
import webbrowser
import config


# ── IT job queries with advanced operators ──────────────────
IT_JOB_QUERIES = [
    # Core dev roles — remote
    '"python developer" remote after:2026-09-01',
    '"django developer" remote after:2026-09-01',
    '"flask developer" remote after:2026-09-01',
    '"full stack developer" remote after:2026-09-01',
    '"backend developer" python remote after:2026-09-01',
    '"software engineer" python remote after:2026-09-01',

    # Location-specific
    '"software developer" Nairobi after:2026-09-01',
    '"python" jobs Kenya after:2026-09-01',
    '"full stack" jobs Nairobi after:2026-09-01',

    # ATS direct — bypass job boards entirely
    'site:boards.greenhouse.io "python" remote',
    'site:jobs.lever.co "python" remote',
    'site:jobs.ashbyhq.com "python" remote',
    'site:apply.workable.com "python developer" remote',

    # Exclude noise — junior roles, recruiters, interns
    '"python developer" remote -junior -intern -recruiter -"commission only" after:2026-09-01',
]


# ── Kenyan local business queries (for org discovery) ───────
LOCAL_BUSINESS_QUERIES = [
    "garage Nairobi",
    "car repair Nairobi",
    "electronics repair Nairobi",
    "phone repair Nairobi",
    "laundry Nairobi",
    "dry cleaner Nairobi",
    "restaurant Nairobi",
    "fashion store Nairobi",
    "hardware store Nairobi",
]


def build_google_jobs_url(query: str) -> str:
    """Build a Google Jobs URL with the ibp=htl;jobs parameter."""
    # URL-encode the query
    encoded = query.replace(" ", "+").replace('"', "%22")
    return f"https://www.google.com/search?q={encoded}&ibp=htl;jobs"


def build_google_maps_url(query: str) -> str:
    """Build a Google Maps search URL."""
    encoded = query.replace(" ", "+")
    return f"https://www.google.com/maps/search/{encoded}"


def open_job_searches() -> None:
    """Open all IT job searches in the browser."""
    print(f"Opening {len(IT_JOB_QUERIES)} Google Jobs searches...\n")
    for q in IT_JOB_QUERIES:
        url = build_google_jobs_url(q)
        webbrowser.open(url)
        print(f"  → {q}")


def open_local_searches() -> None:
    """Open all local business searches in the browser."""
    print(f"\nOpening {len(LOCAL_BUSINESS_QUERIES)} local business searches...\n")
    for q in LOCAL_BUSINESS_QUERIES:
        url = build_google_maps_url(q)
        webbrowser.open(url)
        print(f"  → {q}")


def main():
    import sys

    if "--local" in sys.argv:
        open_local_searches()
    elif "--all" in sys.argv:
        open_job_searches()
        open_local_searches()
    else:
        open_job_searches()

    print("\n✅ Done. Browse each tab and take action manually.")


if __name__ == "__main__":
    main()