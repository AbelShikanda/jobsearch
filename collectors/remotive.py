import requests
from collectors.base import BaseCollector
from models import Job
import config


class RemotiveCollector(BaseCollector):
    name = "remotive"
    URL = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        for term in config.SEARCH_TERMS[:5]:
            try:
                r = requests.get(
                    self.URL,
                    params={"search": term, "limit": 50},
                    timeout=20,
                )
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[{self.name}] '{term}' failed: {e}")
                continue

            for item in data.get("jobs", []):
                title = (item.get("title") or "").strip()
                desc = (item.get("description") or "")[:3000]
                jobs.append(Job(
                    title=title,
                    company=(item.get("company_name") or "").strip(),
                    location=(item.get("candidate_required_location") or "Remote").strip(),
                    url=item.get("url") or "",
                    source=self.name,
                    description=desc,
                    salary=str(item.get("salary") or "").strip(),
                    posted_at=item.get("publication_date") or "",
                ))
        return jobs