import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "followers.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                followers INTEGER NOT NULL,
                delta INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp)"
        )


def get_last_snapshot():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def insert_snapshot(followers: int, delta: int):
    ts = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO snapshots (timestamp, followers, delta) VALUES (?, ?, ?)",
            (ts, followers, delta),
        )
    return ts


def get_history(limit: int = 1440):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT timestamp, followers, delta
            FROM snapshots
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_stats():
    last = get_last_snapshot()
    history = get_history(60)
    total_delta_1h = sum(h["delta"] for h in history)
    return {
        "followers": last["followers"] if last else 0,
        "last_delta": last["delta"] if last else 0,
        "last_update": last["timestamp"] if last else None,
        "total_delta_1h": total_delta_1h,
        "snapshots_count": len(get_history(100000)),
    }
