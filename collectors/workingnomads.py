# collectors/workingnomads.py
import requests
from collectors.base import BaseCollector
from models import Job
import config


class WorkingNomadsCollector(BaseCollector):
    name = "workingnomads"
    URL = "https://www.workingnomads.com/api/exposed_jobs/"

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        try:
            r = requests.get(
                self.URL,
                headers={"User-Agent": "Mozilla/5.0 (job-lead-engine)"},
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[{self.name}] failed: {e}")
            return jobs

        # Response is typically a list of job objects
        items = data if isinstance(data, list) else data.get("jobs", [])
        for item in items:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            jobs.append(Job(
                title=title,
                company=(item.get("company") or item.get("company_name") or "").strip(),
                location=item.get("location", "Remote"),
                url=item.get("url", ""),
                source=self.name,
                description=(item.get("description") or "")[:3000],
                posted_at=item.get("pub_date", item.get("publication_date", "")),
            ))
        return jobs