from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import hashlib


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    salary: str = ""
    posted_at: str = ""
    apply_url: str = ""
    email: str = ""
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    bi_recommendation: str = ""          # replaces `letter`
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def fingerprint(self) -> str:
        key = (
            f"{self.title.lower().strip()}|"
            f"{self.company.lower().strip()}|"
            f"{self.url.strip()}"
        )
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def to_row(self) -> dict:
        return asdict(self) | {"fingerprint": self.fingerprint}