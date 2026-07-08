import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

CSV_PATH = Path(__file__).parent / "data" / "followers.csv"
FIELDS = ("timestamp", "followers", "delta")
GAP_THRESHOLD_SEC = 90


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


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def _distribute_snapshots(prev: dict, followers: int, ts: datetime) -> list[dict]:
    last_ts = _aware(datetime.fromisoformat(prev["timestamp"]))
    ts = _aware(ts)
    elapsed = (ts - last_ts).total_seconds()
    growth = followers - prev["followers"]

    if growth == 0:
        return [{"timestamp": ts.isoformat(), "followers": followers, "delta": 0}]

    if elapsed <= GAP_THRESHOLD_SEC:
        return [{"timestamp": ts.isoformat(), "followers": followers, "delta": growth}]

    minutes = max(1, round(elapsed / 60))
    per_min = growth // minutes
    remainder = growth % minutes

    rows: list[dict] = []
    running = prev["followers"]
    for i in range(minutes):
        delta = per_min + (1 if i < remainder else 0)
        running += delta
        frac = (i + 1) / minutes
        row_ts = last_ts + timedelta(seconds=elapsed * frac)
        rows.append(
            {"timestamp": row_ts.isoformat(), "followers": running, "delta": delta}
        )

    rows[-1]["followers"] = followers
    rows[-1]["delta"] = followers - (
        rows[-2]["followers"] if len(rows) > 1 else prev["followers"]
    )
    return rows


def _write_rows(rows: list[dict]) -> None:
    init_csv()
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        for row in rows:
            writer.writerow(row)


def append_snapshot(followers: int, delta: int) -> str:
    ts = datetime.now(timezone.utc)
    _write_rows([{"timestamp": ts.isoformat(), "followers": followers, "delta": delta}])
    return ts.isoformat()


def append_snapshots(followers: int) -> str:
    last = get_last_snapshot()
    now = datetime.now(timezone.utc)

    if not last:
        return append_snapshot(followers, 0)

    rows = _distribute_snapshots(last, followers, now)
    _write_rows(rows)
    return rows[-1]["timestamp"]


def rebuild_csv() -> int:
    rows = read_all()
    if not rows:
        return 0

    new_rows = [
        {"timestamp": rows[0]["timestamp"], "followers": rows[0]["followers"], "delta": 0}
    ]
    for row in rows[1:]:
        ts = _aware(datetime.fromisoformat(row["timestamp"]))
        new_rows.extend(_distribute_snapshots(new_rows[-1], row["followers"], ts))

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(new_rows)
    return len(new_rows)
