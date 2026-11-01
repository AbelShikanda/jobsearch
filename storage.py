# storage.py
import sqlite3
import config
from models import Job


def _connect():
    return sqlite3.connect(config.DB_PATH)


def init_db() -> None:
    con = _connect()

    # ── Schema ──────────────────────────────────────────────
    con.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            fingerprint        TEXT PRIMARY KEY,
            title              TEXT,
            company            TEXT,
            location           TEXT,
            url                TEXT,
            source             TEXT,
            description        TEXT,
            salary             TEXT,
            posted_at          TEXT,
            apply_url          TEXT,
            email              TEXT,
            score              INTEGER,
            reasons            TEXT,
            bi_recommendation  TEXT,
            user_action        TEXT,
            fetched_at         TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_fp ON jobs(fingerprint)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_company ON jobs(company)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_location ON jobs(location)")

    # ── Lightweight migration: old DBs had a `letter` column ──
    cols = {r[1] for r in con.execute("PRAGMA table_info(jobs)").fetchall()}
    if "bi_recommendation" not in cols:
        con.execute("ALTER TABLE jobs ADD COLUMN bi_recommendation TEXT")
    if "letter" in cols:
        # Copy anything useful across, then leave `letter` in place —
        # dropping columns in SQLite is fragile. It will be ignored.
        con.execute(
            "UPDATE jobs SET bi_recommendation = letter "
            "WHERE bi_recommendation IS NULL"
        )

    con.commit()
    con.close()


def load_seen_fingerprints() -> set[str]:
    con = _connect()
    rows = con.execute("SELECT fingerprint FROM jobs").fetchall()
    con.close()
    return {r[0] for r in rows}


def save_jobs(jobs: list[Job]) -> None:
    con = _connect()
    con.executemany("""
        INSERT OR IGNORE INTO jobs
        (fingerprint, title, company, location, url, source, description,
         salary, posted_at, apply_url, email, score, reasons,
         bi_recommendation, user_action, fetched_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [
        (
            j.fingerprint,
            j.title,
            j.company,
            j.location,
            j.url,
            j.source,
            j.description,
            j.salary,
            j.posted_at,
            j.apply_url,
            j.email,
            j.score,
            "; ".join(j.reasons),
            getattr(j, "bi_recommendation", ""),
            None,
            j.fetched_at,
        )
        for j in jobs
    ])
    con.commit()
    con.close()


def set_user_action(fingerprint: str, action: str) -> None:
    con = _connect()
    con.execute(
        "UPDATE jobs SET user_action = ? WHERE fingerprint = ?",
        (action, fingerprint),
    )
    con.commit()
    con.close()


def get_feedback_rows() -> list[dict]:
    con = _connect()
    cur = con.execute(
        "SELECT description, title, user_action FROM jobs "
        "WHERE user_action IS NOT NULL"
    )
    rows = [
        {"description": r[0], "title": r[1], "user_action": r[2]}
        for r in cur.fetchall()
    ]
    con.close()
    return rows