# collectors/hackernews.py
import re
import requests
from collectors.base import BaseCollector
from models import Job


class HackerNewsCollector(BaseCollector):
    name = "hackernews"

    ALGOLIA = "https://hn.algolia.com/api/v1"
    FIREBASE = "https://hacker-news.firebaseio.com/v0"

    def fetch(self) -> list[Job]:
        jobs: list[Job] = []
        thread_id = self._find_latest_thread()
        if not thread_id:
            print(f"[{self.name}] no 'Who is hiring' thread found")
            return jobs

        try:
            r = requests.get(f"{self.ALGOLIA}/items/{thread_id}", timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[{self.name}] failed to fetch thread: {e}")
            return jobs

        for comment in data.get("children", []):
            text = (comment.get("text") or "").strip()
            if not text or comment.get("dead") or comment.get("deleted"):
                continue

            job = self._parse_comment(text, comment.get("id"))
            if job:
                jobs.append(job)

        print(f"[{self.name}] parsed {len(jobs)} jobs from thread {thread_id}")
        return jobs

    def _find_latest_thread(self) -> str | None:
        """Find the most recent 'Ask HN: Who is hiring?' story by author."""
        try:
            r = requests.get(
                f"{self.ALGOLIA}/search_by_date",
                params={
                    "tags": "story,author_whoishiring",
                    "hitsPerPage": 10,
                },
                timeout=15,
            )
            r.raise_for_status()
            hits = r.json().get("hits", [])
            for hit in hits:
                title = (hit.get("title") or "").lower()
                # Match "who is hiring" but NOT "who wants to be hired" etc.
                if "who is hiring" in title and "wants" not in title:
                    return hit.get("objectID")
        except Exception as e:
            print(f"[{self.name}] thread search failed: {e}")
        return None

    def _parse_comment(self, text: str, comment_id: int) -> Job | None:
        """
        Parse an HN hiring comment.
        Convention: first line = 'Company | Role | Location | URL'
        Fallback: use first line as title, rest as description.
        """
        # Strip HTML entities
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&#x27;", "'", text)
        text = re.sub(r"&#x2F;", "/", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"\s+", " ", text).strip()

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return None

        first_line = lines[0]
        parts = [p.strip() for p in first_line.split("|")]

        title = parts[1] if len(parts) > 1 else first_line[:120]
        company = parts[0] if parts else ""
        location = parts[2] if len(parts) > 2 else "Remote"

        # Extract any URL in the comment
        url_match = re.search(r"https?://[^\s|]+", text)
        url = url_match.group(0) if url_match else f"https://news.ycombinator.com/item?id={comment_id}"

        # Skip if title is too short or doesn't look like a job
        if len(title) < 5:
            return None

        return Job(
            title=title[:120],
            company=company[:100],
            location=location[:60],
            url=url,
            source=self.name,
            description=text[:3000],
        )