"""
Reads feedback and learns weighted keywords.
Applied jobs boost their keywords; ignored jobs suppress theirs.
Writes learned_weights.json.
"""
import json
import re
from pathlib import Path
from collections import Counter
from storage import get_feedback_rows

OUT = Path("learned_weights.json")
TOKEN_RE = re.compile(r"[a-z][a-z\-]{2,}")
STOP = {
    "and", "the", "for", "with", "you", "your", "our", "are", "will",
    "have", "this", "that", "from", "not", "but", "can", "all", "any",
    "job", "work", "team", "role", "years", "experience", "using",
}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOP]


def learn() -> dict[str, int]:
    rows = get_feedback_rows()
    applied = [r for r in rows if r["user_action"] == "applied"]
    ignored = [r for r in rows if r["user_action"] == "ignored"]

    a = Counter(w for r in applied for w in tokenize(r["description"]))
    i = Counter(w for r in ignored for w in tokenize(r["description"]))

    weights: dict[str, int] = {}
    for w, ac in a.items():
        ic = i.get(w, 0)
        if ac >= 3 and ac > ic * 2:
            weights[w] = +5
    for w, ic in i.items():
        ac = a.get(w, 0)
        if ic >= 3 and ic > ac * 2:
            weights[w] = -5

    OUT.write_text(json.dumps(weights, indent=2), encoding="utf-8")
    return weights


def load_weights() -> dict[str, int]:
    if not OUT.exists():
        return {}
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        return {}


if __name__ == "__main__":
    w = learn()
    print(f"✅ Learned {len(w)} weighted tokens → {OUT}")