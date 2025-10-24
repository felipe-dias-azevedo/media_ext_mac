from enum import Enum
from Cocoa import NSUserDefaults


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

    def getNormalization(self) -> str:
        defaults = NSUserDefaults.standardUserDefaults()
        return defaults.stringForKey_(NORMALIZATION_KEY) or self._getDefaultNormalization().value