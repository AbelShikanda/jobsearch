# collectors/serper.py
"""
Serper collector — Google Search for Kenyan job listings.

Uses Serper's /search endpoint with:
  - gl=ke          (geolocation Kenya)
  - location       (Nairobi,Kenya)
  - num=20         (top 20 results per query)

Keeps only results from Kenyan job boards or real company
careers pages. Rejects remote/worldwide listings.
"""
import os
import re
import requests
from collectors.base import BaseCollector
from models import Job
import config


class SerperCollector(BaseCollector):
    name = "serper"
    BASE_URL = "https://google.serper.dev/search"

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise SystemExit(
                "❌ SERPER_API_KEY not set in .env.\n"
                "   Get a free key at https://serper.dev"
            )
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        self._fatal_error = False

    # ── Filters ─────────────────────────────────────────────
    @staticmethod
    def _is_blacklisted(title: str, url: str) -> bool:
        t = (title or "").lower()
        u = (url or "").lower()
        for bad in getattr(config, "SERPER_URL_BLACKLIST", []):
            if bad.lower() in u:
                return True
        for bad in getattr(config, "SERPER_TITLE_BLACKLIST", []):
            if bad.lower() in t:
                return True
        # Reject anything explicitly remote/global
        for bad in getattr(config, "REMOTE_BLACKLIST", []):
            if bad in t:
                return True
        return False

    @staticmethod
    def _is_whitelisted(url: str) -> bool:
        u = (url or "").lower()
        for good in getattr(config, "SERPER_URL_WHITELIST", []):
            if good.lower() in u:
                return True
        return False

    @staticmethod
    def _extract_company(title: str, snippet: str) -> str:
        """Best-effort: pull company name out of a job-board title."""
        # Common patterns: "Job Title at Company", "Job Title - Company"
        m = re.search(r"\bat\s+([A-Z][\w&\.\- ]{2,50})", title)
        if m:
            return m.group(1).strip()
        # Fall back to the first sentence of the snippet
        if snippet:
            first = snippet.split(".")[0].strip()
            if 3 < len(first) < 60:
                return first
        return ""

    # ── Main fetch ──────────────────────────────────────────
    def fetch(self) -> list[Job]:
        if not getattr(config, "SERPER_ENABLED", True):
            print(f"[{self.name}] disabled in config — skipping")
            return []

        if self._fatal_error:
            print(f"[{self.name}] previous fatal error — skipping")
            return []

        jobs: list[Job] = []
        seen_urls = set()

        terms = config.SEARCH_TERMS[:getattr(config, "SERPER_MAX_TERMS", 5)]
        location = getattr(config, "SERPER_LOCATION", "Nairobi, Kenya")

        for term in terms:
            # Kenyan-local query
            query = f"{term} jobs {location}"

            try:
                r = requests.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json={
                        "q": query,
                        "num": 20,
                        "gl": "ke",
                        "hl": "en",
                        "location": location,
                    },
                    timeout=20,
                )
            except requests.exceptions.Timeout:
                print(f"[{self.name}] timeout on '{term}' — skipping")
                continue
            except requests.exceptions.RequestException as e:
                print(f"[{self.name}] network error on '{term}': {e}")
                continue

            if r.status_code == 400:
                print(f"[{self.name}] ⚠️ pattern not allowed on free tier "
                      f"for '{term}' — skipping")
                continue

            if r.status_code in (401, 403):
                print(f"[{self.name}] ❌ auth failed ({r.status_code}) — "
                      f"check SERPER_API_KEY. Stopping.")
                self._fatal_error = True
                return jobs

            if r.status_code == 402:
                print(f"[{self.name}] ❌ credits exhausted (402) — "
                      f"top up at https://serper.dev. Stopping.")
                self._fatal_error = True
                return jobs

            if r.status_code == 429:
                print(f"[{self.name}] ⚠️ rate limited on '{term}' — skipping")
                continue

            if not r.ok:
                print(f"[{self.name}] HTTP {r.status_code} on '{term}': "
                      f"{r.text[:120]}")
                continue

            try:
                data = r.json()
            except ValueError:
                continue

            kept = 0
            for item in data.get("organic", []):
                title = (item.get("title") or "").strip()
                url = (item.get("link") or "").strip()
                snippet = (item.get("snippet") or "").strip()
                if not title or not url:
                    continue
                if url in seen_urls:
                    continue

                if self._is_blacklisted(title, url):
                    continue

                # Keep only URLs that look like real job pages
                if not self._is_whitelisted(url):
                    if not any(k in url for k in
                               ("/job/", "/jobs/", "/careers/",
                                "/vacancy/", "/vacancies/", "?job")):
                        continue

                seen_urls.add(url)

                jobs.append(Job(
                    title=title[:120],
                    company=self._extract_company(title, snippet)[:100],
                    location="Nairobi",
                    url=url,
                    source=self.name,
                    description=snippet[:3000],
                    posted_at=item.get("date") or "",
                ))
                kept += 1

            print(f"[{self.name}] '{term}': {kept} kept")

        print(f"[{self.name}] {len(jobs)} jobs")
        return jobs