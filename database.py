import sqlite3
import time
from typing import List, Dict, Any, Optional

DB_FILENAME = "media.db"

class MediaDB:
    """
    SQLite helper for ./media.db with a single table: history.

    Table schema:
      - id INTEGER PRIMARY KEY AUTOINCREMENT
      - file TEXT NOT NULL
      - url  TEXT NOT NULL
      - ts   INTEGER NOT NULL  (Unix epoch seconds)

    Methods:
      - insert_history(file, url, ts=None) -> int
      - select_history() -> List[Dict[str, Any]]
    """

    def __init__(self, db_path: str = "./media.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Initialize schema
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                file TEXT    NOT NULL,
                url  TEXT    NOT NULL,
                ts   INTEGER NOT NULL
            )
        """)
        # Helpful index for time-ordered queries
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_history_ts ON history(ts)")
        self.conn.commit()

    # context-manager niceties
    def __enter__(self) -> "MediaDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if getattr(self, "conn", None):
            self.conn.close()
            self.conn = None

    # --- API dedicated to the `history` table ---
    def insert_history(self, file: str, url: str, ts: Optional[int] = None) -> int:
        """
        Insert one history row. If `ts` is None, uses current Unix epoch seconds.
        Returns the inserted row id.
        """
        if ts is None:
            ts = int(time.time())

        cur = self.conn.execute(
            "INSERT INTO history (file, url, ts) VALUES (?, ?, ?)",
            (file, url, int(ts)),
        )
        self.conn.commit()
        return int(cur.lastrowid or 0)

    def select_history(self, newest_first: bool = True) -> List[Dict[str, Any]]:
        
        order = "DESC" if newest_first else "ASC"
        sql = f"SELECT id, file, url, ts FROM history ORDER BY ts {order}"
        rows = self.conn.execute(sql).fetchall()
        return [dict(r) for r in rows]


# --- Example usage ---
if __name__ == "__main__":
    db = MediaDB()
    new_id = db.insert_history(file="example.mp4", url="https://example.com/video")
    print("Inserted id:", new_id)

    all_rows = db.select_history()
    print(all_rows)
    db.close()
