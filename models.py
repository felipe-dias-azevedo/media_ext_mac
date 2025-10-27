import time
from datetime import datetime
from typing import Dict, Iterable, List

class MediaItem(object):
    __slots__ = ("title", "timestamp", "isGroup")
    def __init__(self, title="", timestamp="", isGroup=False):
        self.title = title
        self.timestamp = timestamp
        self.isGroup = isGroup

    @classmethod
    def group(cls, groupTitle):
        return cls(title=groupTitle, timestamp="", isGroup=True)

    @classmethod
    def item(cls, title, timestamp):
        return cls(title=title, timestamp=timestamp, isGroup=False)
    
class HistoryFormatter:

    _now = int(time.time())

    _DAY   = 24 * 60 * 60
    _WEEK  = 7  * _DAY
    _MONTH = 30 * _DAY
    _YEAR  = 365 * _DAY

    _GROUPS = [
        ("Last 24 hours", (0, _DAY)),
        ("Last 7 days", (_DAY, _WEEK)),
        ("Last 30 days", (_WEEK, _MONTH)),
        ("Last 365 days", (_MONTH, _YEAR)),
        ("Long time ago",( _YEAR, 10**12)),
    ]

    def format(self, rows: Iterable[MediaItem]) -> List[MediaItem]:
        
        buckets: Dict[str, List[MediaItem]] = {label: [] for label, _ in self._GROUPS}

        for r in rows:
            ts = int(r["ts"])
            age = max(0, self._now - ts)  # guard against clock skew
            for label, (lo, hi) in self._GROUPS:
                if lo <= age < hi:
                    buckets[label].append(MediaItem.item(r["file"], datetime.fromtimestamp(ts).strftime("%y/%m/%d, %H:%M:%S")))
                    break

        out: List[MediaItem] = []
        for label, _ in self._GROUPS:
            group_rows = buckets[label]
            if not group_rows:
                continue
            # newest first within the group
            # group_rows.sort(key=lambda x: int(x["ts"]), reverse=True)
            out.append(MediaItem.group(label))
            out.extend(group_rows)
        return out
