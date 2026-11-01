# collectors/brightdata_maps.py
"""
Bright Data SERP collector — finds Nairobi organizations via
google.com/search.

Uses the `source` field (business name from Google's knowledge
graph) before falling back to `title`. Filters out category
pages, stubs, directories, government portals, and multinationals.

Each Job's description is prefixed with the search category so
that bi_advisor.py can build a sector-specific memo:
    "Category: pharmacy | Goodlife Pharmacy is Kenya's largest..."
"""
import os
import re
import json
import time
import urllib.parse
import requests
from collectors.base import BaseCollector
from models import Job
import config


# ── Domains that are never a business ───────────────────────
ARTICLE_DOMAINS = (
    "medium.com", "reddit.com", "quora.com", "youtube.com",
    "wikipedia.org", "facebook.com", "twitter.com", "x.com",
    "instagram.com", "tiktok.com", "linkedin.com",
    "blogspot.com", "wordpress.com", "substack.com",
    "citizen.digital", "standardmedia.co.ke", "nation.africa",
    "the-star.co.ke", "businessdailyafrica.com", "kbc.co.ke",
    "ktnnews.co.ke", "citizentv.co.ke", "theeastafrican.co.ke",
    "kenyanwallstreet.com", "capitalfm.co.ke", "hivisasa.com",
    "yellowpageskenya.com", "kenyaplex.com", "yellowpages.co.ke",
    "tripadvisor.com", "yelp.com", "foursquare.com",
    "businesslist.co.ke", "kenyabusinessdirectory.co.ke",
    "carpages.co.ke", "kenyapages.co.ke",
    "jiji.co.ke", "olx.co.ke", "pigia.me", "cheki.co.ke",
    "autochek.africa", "cars45.co.ke",
    "glassdoor.com", "indeed.com",
    "brightermonday.co.ke", "fuzu.com", "myjobmag.co.ke",
    "google.com", "maps.google.com", "goo.gl",
    "cak.go.ke", "ca.go.ke", "kebs.org", "kra.go.ke",
    # Directories that slipped through
    "ruzave.com", "goodfirms.co", "clutch.co",
    "truehost.co.ke", "whogohost.com",
    # International directories / mapping / data brokers
    "zoominfo.com", "medpages.co.za", "viamichelin.com",
    "mylpg.eu", "pinterest.",
)

# ── Title patterns that mean "article, not a business" ──────
ARTICLE_TITLE_PATTERNS = (
    "top 10", "top 5", "top 20", "top 27", "top 16", "top 17",
    "top 30", "top 50", "top 100",
    "best ", "cheapest ", "affordable ", "most ",
    "guide to", "guide for", "how to", "what is", "why ",
    "list of", "list-of", "everything you", "you need to know",
    "here are the", "these are the", "find the",
    "comparison", " vs ", "review of", "reviews of",
    "directory", "yellow pages", "listings",
    "news", "breaking", "explainer", "watch:",
    "for rent", "for sale", "to let", "to lease",
    "near me", "near you", "around me",
    "driving directions to", "directions to ",
    "opening hours", "reviews of",
    "salary", "careers at", "jobs at", "hiring",
    "vacancy", "vacancies", "internship",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    "list-of-", "-list-", "-report", "_report",
    "education in", "shopping in", "shopping list",
    "transport in", "transportation in",
    "where can i", "where to find",
    "providers contact", "providers contacts",
    "approved panel", "licensed postal",
    "category:", "category ",
    "find a branch", "find a store", "find a ",
    "the finest", "the best", "the leading",
    "your one stop", "your trusted",
)

# ── Clean title stubs — reject immediately ──────────────────
STUB_TITLES = {
    "home", "contact us", "contact", "about us", "about",
    "who we are", "what we do", "services", "our services",
    "products", "our products", "firms", "companies",
    "shop", "store", "welcome", "index", "main page",
    "site map", "sitemap", "privacy policy",
    "terms of service", "terms and conditions",
    "tyres", "courier service", "courier services",
    "couriers services", "fuel business",
    "suppliers", "distributors & stockists",
    "diagnostic imaging", "dental care", "dental services",
    "medical imaging", "kenya",
    "warehousing companies in kenya",
    "warehousing in mombasa & nairobi",
    "medical equipment", "medical equipment supplies",
    "pharmacy services", "pharmacies & chemists",
    "freight forwarders kenya", "shipping companies in kenya",
    "clearing and forwarding",
    "cargo warehouses in nairobi, kenya",
    "our nairobi warehouse in kenya",
    "water service providers",
    "bulk clean water delivery in kenya",
    "clean water tanker supply services in nairobi",
    "solar system installers in kenya",
    "solar installation company in kenya",
    "top solar energy solutions in nairobi, kenya by solargen",
    "nairobi garage // connect cowork create // flexible working",
    "car garage & service centre nairobi",
    "kenya national bureau of statistics",
    "nairobi garage",
    "kericho", "kisumu", "mombasa", "africa",
    "magical kenya",
    "take app", "mahitaji", "shell locations",
}

# ── URL path fragments that mean "category page, not a business"
JUNK_URL_PATHS = (
    "/category/", "/categories/", "/tag/", "/tags/",
    "/page/", "/search", "?s=", "&s=",
    "/feed/", "/rss/", "/wp-json/",
    "/list-of-", "/directory/", "/listings/",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
)

# ── Name ending in a domain — this is a URL, not a business ─
DOMAIN_SUFFIX_RE = re.compile(
    r"\.(com|co\.ke|ke|org|net|io|info|biz|africa|online|"
    r"shop|store|eu|tv|us|co|app|dev|ai|tech)(\s|$)",
    re.I,
)

# ── Name starting with country/city + generic noun ──────────
GENERIC_NAME_RE = re.compile(
    r"^(kenya|nairobi|mombasa|africa|east africa)\s+"
    r"(trade|business|portal|directory|traders?|tradex|"
    r"magical|services?|schools?)\b",
    re.I,
)

# ── Multinationals / NGOs / governments — not local SMBs ────
MULTINATIONAL_BLACKLIST = (
    "un world food", "world food programme", "unicef", "undp",
    "international criminal court", "international monetary",
    "centers for disease control", "cdc", "who ", "world health",
    "the guardian", "bbc", "cnn", "reuters",
    "mol logistics", "dhl", "fedex", "ups ",
    "g4s global", "g4s ",
    "shell locations", "total energies", "british american",
    "africa tech schools",
    # International directories / data brokers
    "zoominfo", "medpages", "viamichelin", "mylpg",
)

# ── Acronyms to preserve during Title Case cleanup ──────────
PRESERVE_ACRONYMS = {
    "CP", "RCL", "KM", "KWAL", "KPLC", "KBS", "KRA", "KEBS",
    "SACCO", "NGO", "ICT", "IT", "CEO", "CFO", "CTO",
    "NTSA", "NHIF", "NSSF", "KCB", "NCBA", "ABSA",
}


class BrightDataMapsCollector(BaseCollector):
    name = "brightdata_maps"
    BASE_URL = "https://api.brightdata.com/request"

    def __init__(self):
        self.api_key = os.getenv("BRIGHTDATA_API_KEY")
        self.zone = os.getenv("BRIGHTDATA_ZONE")

        if not self.api_key:
            raise SystemExit(
                "❌ BRIGHTDATA_API_KEY not set in .env.\n"
                "   Get a free key at https://brightdata.com"
            )
        if not self.zone:
            raise SystemExit(
                "❌ BRIGHTDATA_ZONE not set in .env.\n"
                "   Create a SERP API zone in your Bright Data dashboard."
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self._fatal_error = False
        self._debug_printed = False

    # ── Junk detection ──────────────────────────────────────
    def _is_junk(self, item: dict, name: str) -> bool:
        name_l = name.lower()
        link = (item.get("link") or "").lower()
        title = (item.get("title") or "").lower()

        # Domain check
        if any(d in link for d in ARTICLE_DOMAINS):
            return True

        # Category / tag URL check
        if any(p in link for p in JUNK_URL_PATHS):
            return True

        # Article pattern on name + title
        combined = f"{name_l} {title}"
        if any(p in combined for p in ARTICLE_TITLE_PATTERNS):
            return True

        # Stub title check
        if name_l in STUB_TITLES:
            return True

        # Name is just a domain
        if DOMAIN_SUFFIX_RE.search(name_l):
            return True

        # Name starts with "kenya <generic>"
        if GENERIC_NAME_RE.match(name_l):
            return True

        # Multinational / NGO / gov
        if any(m in name_l for m in MULTINATIONAL_BLACKLIST):
            return True

        # Leading pipe (broken source field)
        if name.startswith("|"):
            return True

        # Middle-dot profile marker (Pinterest / social profiles)
        if " · " in name:
            return True

        # Length checks
        if len(name) > 60:
            return True
        if name.count(".") > 1:
            return True

        # Phone number in name
        if re.search(r"0\d{2}[\s\-]?\d{3}[\s\-]?\d{3,4}", name):
            return True

        # Word count — business names are short
        words = name_l.split()
        if len(words) > 7:
            return True

        # Domain must be real
        if not re.match(r"https?://[^/]+\.[a-z]{2,}", link):
            return True

        return False

    # ── Pick the best name from a SERP result ───────────────
    def _pick_name(self, item: dict) -> str:
        """
        Prefer `source` (Google's knowledge graph business name).
        Fall back to `title`. Apply cosmetic cleanup.
        """
        source = (item.get("source") or "").strip()
        if source and 3 <= len(source) <= 60:
            cleaned = re.split(
                r"\s+[\-\|–—]\s+", source, maxsplit=1
            )[0]
            name = cleaned.strip()[:100]
        else:
            title = (item.get("title") or "").strip()
            title = re.split(
                r"\s+[\-\|–—:]\s+", title, maxsplit=1
            )[0]
            name = title.strip()[:100]

        # ── Cosmetic cleanup ────────────────────────────────
        name = name.rstrip(".,;:").strip()

        # All-caps or all-lowercase → Title Case
        if name and (name == name.upper() or name == name.lower()):
            parts = name.split()
            parts = [
                p.upper() if p.upper() in PRESERVE_ACRONYMS
                else p.capitalize()
                for p in parts
            ]
            name = " ".join(parts)

        return name

    # ── Main fetch ──────────────────────────────────────────
    def fetch(self) -> list[Job]:
        if not getattr(config, "BRIGHTDATA_ENABLED", True):
            print(f"[{self.name}] disabled in config — skipping")
            return []

        if self._fatal_error:
            print(f"[{self.name}] previous fatal error — skipping")
            return []

        orgs: list[Job] = []
        categories = getattr(config, "ORG_CATEGORIES", [])
        max_terms = getattr(config, "BRIGHTDATA_MAX_TERMS", 10)
        location = getattr(
            config, "BRIGHTDATA_LOCATION", "Nairobi, Kenya"
        )

        for category in categories[:max_terms]:
            query = f"{category} {location}"
            search_url = (
                "https://www.google.com/search?q="
                f"{urllib.parse.quote_plus(query)}&gl=ke&hl=en"
            )

            payload = {
                "zone": self.zone,
                "url": search_url,
                "format": "json",
                "data_format": "parsed",
            }

            wrapper = None
            for attempt in (1, 2):
                try:
                    r = requests.post(
                        self.BASE_URL,
                        headers=self.headers,
                        json=payload,
                        timeout=90,
                    )
                except requests.exceptions.Timeout:
                    if attempt == 1:
                        continue
                    print(f"[{self.name}] timeout on '{category}' "
                          f"— skipping")
                    break
                except requests.exceptions.RequestException as e:
                    print(f"[{self.name}] network error on "
                          f"'{category}': {e}")
                    break

                if r.status_code in (401, 403):
                    print(f"[{self.name}] ❌ auth failed — stopping")
                    self._fatal_error = True
                    return orgs

                if r.status_code == 429:
                    print(f"[{self.name}] ⚠️ rate limited — "
                          f"sleeping 10s")
                    time.sleep(10)
                    break

                if not r.ok:
                    print(f"[{self.name}] HTTP {r.status_code} on "
                          f"'{category}'")
                    break

                try:
                    wrapper = r.json()
                except ValueError:
                    print(f"[{self.name}] invalid JSON for "
                          f"'{category}'")
                    break

                status = wrapper.get("status_code", 200)
                body_str = wrapper.get("body")
                if status != 200 or not body_str:
                    hdrs = wrapper.get("headers") or {}
                    err_code = hdrs.get(
                        "x-brd-error-code", "unknown"
                    )

                    if err_code == "captcha" and attempt == 1:
                        print(f"[{self.name}] captcha on "
                              f"'{category}' — retrying after 15s")
                        time.sleep(15)
                        wrapper = None
                        continue

                    print(f"[{self.name}] skip '{category}': "
                          f"status={status} brd_error={err_code}")
                    wrapper = None
                    break

                break

            if wrapper is None:
                continue

            try:
                data = json.loads(wrapper["body"])
            except (ValueError, TypeError, KeyError):
                continue

            results = (
                data.get("organic")
                or data.get("results")
                or []
            )

            if results and not self._debug_printed:
                print(f"[{self.name}] DEBUG first result keys: "
                      f"{list(results[0].keys())}")
                self._debug_printed = True

            kept = 0
            skipped = 0
            for item in results:
                name = self._pick_name(item)
                if not name or len(name) < 3:
                    skipped += 1
                    continue

                if self._is_junk(item, name):
                    skipped += 1
                    continue

                link = item.get("link") or search_url
                snippet = (
                    item.get("description")
                    or item.get("snippet")
                    or ""
                ).strip()

                # Prepend the search category so bi_advisor.py
                # can build a sector-specific memo.
                orgs.append(Job(
                    title=name[:120],
                    company=name[:100],
                    location="Nairobi",
                    url=link,
                    source=self.name,
                    description=(
                        f"Category: {category} | "
                        f"{snippet[:900]}"
                    ),
                ))
                kept += 1

            print(f"[{self.name}] '{category}': "
                  f"{kept} kept, {skipped} filtered")

            time.sleep(5)

        print(f"[{self.name}] {len(orgs)} organizations")
        return orgs