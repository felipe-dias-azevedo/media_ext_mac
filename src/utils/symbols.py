
from AppKit import (
    NSFontWeightMedium,
    NSImage,
    NSImageSymbolConfiguration,
)

def create_symbol(name: str, point_size: float = 14.0):
    conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_(
        point_size,
        NSFontWeightMedium,
    )

    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
        name,
        None,
    )

    return image.imageWithSymbolConfiguration_(conf)