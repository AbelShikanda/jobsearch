# sites.py
"""
Config-driven site definitions for ConfigDrivenCollector.

KENYA-ONLY. Every entry targets a Kenyan job board.
All entries default `location` to "Kenya" so the local gate
in qualification.py passes even without a location selector.
"""

SITES = [
    # ── BrighterMonday Kenya ────────────────────────────────
    {
        "name": "brightermonday",
        "url": "https://www.brightermonday.co.ke/jobs",
        "wait_for": "[data-cy='listing-title-link']",
        "extra_wait_ms": 3000,
        "card_selector": "a[data-cy='listing-title-link']",
        "title_selector": "p",
        "link_selector": "",
        "company_selector": "",
        "location_selector": "",
        "company": "",
        "location": "Kenya",
    },

    # ── BrighterMonday — IT & Software category ─────────────
    {
        "name": "brightermonday_it",
        "url": "https://www.brightermonday.co.ke/jobs/it-software",
        "wait_for": "[data-cy='listing-title-link']",
        "extra_wait_ms": 3000,
        "card_selector": "a[data-cy='listing-title-link']",
        "title_selector": "p",
        "link_selector": "",
        "company_selector": "",
        "location_selector": "",
        "company": "",
        "location": "Kenya",
    },

    # ── Fuzu Kenya ──────────────────────────────────────────
    {
        "name": "fuzu",
        "url": "https://www.fuzu.com/kenya/job",
        "wait_for": "a[href*='/kenya/jobs/']",
        "extra_wait_ms": 5000,
        "card_selector": "a[href*='/kenya/jobs/']",
        "title_selector": "",
        "link_selector": "",
        "company_selector": "",
        "location_selector": "",
        "company": "",
        "location": "Kenya",
    },

    # ── MyJobMag Kenya ──────────────────────────────────────
    {
        "name": "myjobmag",
        "url": "https://www.myjobmag.co.ke/jobs",
        "wait_for": "li.job-list-li, article, div[class*='job']",
        "card_selector": "li.job-list-li, article.job-list-li",
        "title_selector": "h2 a, h3 a",
        "link_selector": "h2 a, h3 a",
        "company_selector": "[class*='company']",
        "location_selector": "[class*='location']",
        "company": "",
        "location": "Kenya",
    },
]