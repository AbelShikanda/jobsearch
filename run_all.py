"""
Single entry point: parse resume, then run the search.
Schedule THIS file with cron / Task Scheduler.
"""
import sys
from parse_resume import refresh_profile

if __name__ == "__main__":
    refresh_profile(force="--force-resume" in sys.argv)
    print("▶ Resume profile ready")
    from main import run
    import asyncio
    asyncio.run(run(
        force_resume=False,
        dry_run="--dry-run" in sys.argv,
    ))