# collectors/crossover.py — placeholder
import requests
from collectors.base import BaseCollector
from models import Job
import config


class CrossoverCollector(BaseCollector):
    name = "crossover"
    URL = "https://www.crossover.com/api/jobs"  # ← verify in DevTools

    def fetch(self) -> list[Job]:
        jobs = []
        try:
            r = requests.get(self.URL, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[{self.name}] failed: {e}")
            return jobs

        for item in data.get("jobs", []):
            title = item.get("title", "")
            if not self._matches(title):
                continue
            jobs.append(Job(
                title=title,
                company=item.get("company", "Crossover"),
                location=item.get("location", "Remote"),
                url=item.get("url", ""),
                source=self.name,
            ))
        return jobs

    def _matches(self, text: str) -> bool:
        t = text.lower()
        return any(term.lower() in t for term in config.SEARCH_TERMS)