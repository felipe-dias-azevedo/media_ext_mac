from __future__ import annotations

from pathlib import Path
import sys

from PyQt6.QtGui import QColor, QIcon
import qtawesome as qta

_BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
_APP_ICON_NAME = "icon_borderless_1024.png" if sys.platform == "win32" else "icon_1024.png"
_APP_ICON_PATH = _BUNDLE_ROOT / "icon" / _APP_ICON_NAME

_QTA_NAMES = {
    "checkmark.circle.fill": "fa6s.circle-check",
    "xmark.circle.fill": "fa6s.circle-xmark",
    "doc.on.clipboard": "fa6.paste",
    "gearshape": "fa6s.gear",
    "chevron.down": "fa5s.chevron-down",
    "folder.open": "fa6.folder-open",
}

_symbol_icon_cache: dict[tuple[str, str], QIcon] = {}


def app_icon() -> QIcon:
    return QIcon(str(_APP_ICON_PATH))


def create_symbol(name: str, color: QColor | None = None) -> QIcon:
    """Return a cached qtawesome icon for one of this app's symbol names."""
    color = QColor(color) if color is not None else QColor(142, 142, 147)
    cache_key = (name, color.name(QColor.NameFormat.HexArgb))
    cached = _symbol_icon_cache.get(cache_key)
    if cached is not None:
        return cached

    icon = qta.icon(_QTA_NAMES[name], color=color)
    _symbol_icon_cache[cache_key] = icon
    return icon
