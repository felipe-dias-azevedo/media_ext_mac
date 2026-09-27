from enum import Enum

from PyQt6.QtCore import QSettings


class Normalization(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

NORMALIZATION_KEY = "NormalizationFrequency"
NORMALIZATION_OPTIONS = [Normalization.LOW, Normalization.MEDIUM, Normalization.HIGH]

class UserDefaults():
    @staticmethod
    def _getDefaultNormalization():
        return NORMALIZATION_OPTIONS[-1]

    @staticmethod
    def _settings():
        return QSettings(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            "MediaExt",
            "MediaExt",
        )

    def getNormalization(self) -> str:
        default = self._getDefaultNormalization().value
        normalization = self._settings().value(NORMALIZATION_KEY, default)
        options = [option.value for option in NORMALIZATION_OPTIONS]
        return normalization if normalization in options else default
    
    def setNormalization(self, normalization: str):
        settings = self._settings()
        settings.setValue(NORMALIZATION_KEY, normalization)
        settings.sync()