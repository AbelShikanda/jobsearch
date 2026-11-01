import requests
from collectors.base import BaseCollector
from models import Job
import config


class ArbeitnowCollector(BaseCollector):
    name = "arbeitnow"
    URL = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        try:
            r = requests.get(self.URL, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[{self.name}] failed: {e}")
            return jobs

        for item in data.get("data", []):
            title = (item.get("title") or "").strip()
            desc = (item.get("description") or "")[:3000]
            if not self._matches(f"{title} {desc}"):
                continue
            jobs.append(Job(
                title=title,
                company=(item.get("company_name") or "").strip(),
                location=(item.get("location") or "Remote").strip(),
                url=item.get("url") or "",
                source=self.name,
                description=desc,
                posted_at=str(item.get("created_at") or ""),
            ))
        return jobs

    def _matches(self, text: str) -> bool:
        t = text.lower()
        return any(skill in t for skill in config.STRONG_SKILLS)