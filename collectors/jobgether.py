# collectors/jobgether.py
import requests
from collectors.base import BaseCollector
from models import Job
import config


class JobgetherCollector(BaseCollector):
    name = "jobgether"
    URL = "https://jobgether.com/astroapi/ai/jobs.json"

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        for term in config.SEARCH_TERMS[:3]:
            try:
                r = requests.get(
                    self.URL,
                    params={
                        "keyword": term,
                        "limit": 25,
                        "sort": "date",
                    },
                    timeout=20,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[{self.name}] '{term}' failed: {e}")
                continue

            for item in data.get("jobs", []):
                title = (item.get("title") or "").strip()
                if not title:
                    continue
                jobs.append(Job(
                    title=title,
                    company=(item.get("company") or {}).get("name", "") if isinstance(item.get("company"), dict) else item.get("company", ""),
                    location=item.get("location", "Remote"),
                    url=item.get("url", ""),
                    source=self.name,
                    description=(item.get("description") or "")[:3000],
                    posted_at=item.get("publishedAt", ""),
                ))
        return jobs