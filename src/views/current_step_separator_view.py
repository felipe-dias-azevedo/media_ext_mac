import objc

from AppKit import (
    NSLayoutConstraint,
    NSBox,
    NSColor,
    NSMakeRect,
    NSView,
    NSBoxCustom,
)


# ============================================================
# Separator
# ============================================================

class CurrentStepSeparator(NSView):

    def init(self):
        self = objc.super(CurrentStepSeparator, self).init()
        if self is None:
            return None

        line = NSBox.alloc().initWithFrame_(NSMakeRect(0, 0, 0, 1))
        line.setBoxType_(NSBoxCustom)
        line.setBorderWidth_(0.0)
        line.setFillColor_(NSColor.separatorColor())
        line.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.addSubview_(line)

        NSLayoutConstraint.activateConstraints_([
            line.leadingAnchor().constraintEqualToAnchor_(
                self.leadingAnchor()
            ),
            line.trailingAnchor().constraintEqualToAnchor_(
                self.trailingAnchor()
            ),
            line.centerYAnchor().constraintEqualToAnchor_(
                self.centerYAnchor()
            ),
            line.heightAnchor().constraintEqualToConstant_(1),
        ])

        return self
