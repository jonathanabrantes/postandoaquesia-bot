import csv
from datetime import datetime, timezone
from pathlib import Path

CSV_PATH = Path(__file__).parent / "data" / "followers.csv"
FIELDS = ("timestamp", "followers", "delta")


def init_csv():
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()


def read_all() -> list[dict]:
    init_csv()
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return [
            {
                "timestamp": row["timestamp"],
                "followers": int(row["followers"]),
                "delta": int(row["delta"]),
            }
            for row in csv.DictReader(f)
        ]


def get_last_snapshot() -> dict | None:
    rows = read_all()
    return rows[-1] if rows else None


def append_snapshot(followers: int, delta: int) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    init_csv()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=FIELDS).writerow(
            {"timestamp": ts, "followers": followers, "delta": delta}
        )
    return ts
