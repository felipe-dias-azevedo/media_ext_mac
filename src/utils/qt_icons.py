from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QColor, QIcon
import qtawesome as qta

_APP_ICON_PATH = Path(__file__).resolve().parents[2] / "icon" / "icon_1024.png"

_QTA_NAMES = {
    "checkmark.circle.fill": "fa5s.check-circle",
    "xmark.circle.fill": "fa5s.times-circle",
    "doc.on.clipboard": "fa5s.paste",
    "gearshape": "fa5s.cog",
    "chevron.down": "fa5s.chevron-down",
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
