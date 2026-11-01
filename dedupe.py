from models import Job


def dedupe(jobs: list[Job], seen_fingerprints: set[str]) -> list[Job]:
    fresh, batch_seen = [], set()
    for j in jobs:
        fp = j.fingerprint
        if fp in seen_fingerprints or fp in batch_seen:
            continue
        batch_seen.add(fp)
        fresh.append(j)
    return fresh