"""
Mark jobs as applied / ignored / rejected.

Usage:
    python feedback.py <fingerprint> applied
    python feedback.py <fingerprint> ignored
"""
import sys
from storage import init_db, set_user_action

VALID = {"applied", "ignored", "rejected"}


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[2] not in VALID:
        print("Usage: python feedback.py <fingerprint> "
              "{applied|ignored|rejected}")
        return 1
    init_db()
    set_user_action(argv[1], argv[2])
    print(f"✅ Marked {argv[1]} as {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))