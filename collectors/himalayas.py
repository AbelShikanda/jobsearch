# collectors/himalayas.py
import requests
from collectors.base import BaseCollector
from models import Job
import config


class HimalayasCollector(BaseCollector):
    name = "himalayas"
    URL = "https://himalayas.app/jobs/api/search"

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        # Use the first few search terms to keep it fast
        for term in config.SEARCH_TERMS[:5]:
            try:
                r = requests.get(
                    self.URL,
                    params={
                        "q": term,
                        "limit": 20,
                        "worldwide": "true",  # <--- THIS IS THE FIX
                    },
                    headers={"User-Agent": "Mozilla/5.0 (job-lead-engine)"},
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
                
                # Double-check the location restrictions just to be safe
                # If the list is not empty, skip it (redundant, but safe)
                restrictions = item.get("locationRestrictions")
                if restrictions:  # If this is not None/empty, it's not truly worldwide
                    continue

                jobs.append(Job(
                    title=title,
                    company=(item.get("companyName") or "").strip(),
                    location="Worldwide",  # Hardcoded for clarity
                    url=item.get("applicationLink") or item.get("guid", ""),
                    source=self.name,
                    description=(item.get("description") or "")[:3000],
                    salary=self._format_salary(item),
                    posted_at=item.get("pubDate", ""),
                ))
        return jobs

    @staticmethod
    def _format_salary(item: dict) -> str:
        mn = item.get("minSalary")
        mx = item.get("maxSalary")
        cur = item.get("currency", "USD")
        per = item.get("salaryPeriod", "annual")
        if not mn and not mx:
            return ""
        if mn and mx and mn != mx:
            return f"{cur} {mn}-{mx}/{per}"
        return f"{cur} {mn or mx}/{per}"