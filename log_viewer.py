import objc
from Cocoa import (
    NSView, NSBox, NSTextView, NSFont, NSColor,
    NSMakeSize, NSMakeRange, NSLayoutConstraint, NSBoxCustom,
    NSTextLayoutOrientationHorizontal,
)


class LogViewer(NSView):

    def init(self):
        self = objc.super(LogViewer, self).init()
        if self is None:
            return None

        self.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.logContainer = NSBox.alloc().init()
        self.logContainer.setBoxType_(NSBoxCustom)
        self.logContainer.setCornerRadius_(8.0)
        self.logContainer.setBorderWidth_(1.0)
        self.logContainer.setBorderColor_(NSColor.separatorColor())
        self.logContainer.setFillColor_(NSColor.controlBackgroundColor())
        self.logContainer.setContentViewMargins_(NSMakeSize(0.0, 0.0))
        self.logContainer.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.logScroll = NSTextView.scrollablePlainDocumentContentTextView()
        self.logScroll.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.logText = self.logScroll.documentView()
        self.logText.setEditable_(False)
        self.logText.setSelectable_(True)
        self.logText.setRichText_(False)
        self.logText.setLayoutOrientation_(NSTextLayoutOrientationHorizontal)
        self.logText.setFont_(NSFont.userFixedPitchFontOfSize_(NSFont.smallSystemFontSize()))
        self.logText.setTextColor_(NSColor.labelColor())
        self.logText.setDrawsBackground_(False)
        self.logText.setTextContainerInset_(NSMakeSize(10.0, 10.0))
        if self.logText.textContainer() is not None:
            self.logText.textContainer().setWidthTracksTextView_(True)
            self.logText.textContainer().setContainerSize_(NSMakeSize(0.0, float("inf")))
        self.logText.setString_("")

        self.logScroll.setCornerRadius_(8.0)

        logContent = self.logContainer.contentView()
        logContent.addSubview_(self.logScroll)

        self.addSubview_(self.logContainer)

        NSLayoutConstraint.activateConstraints_([
            self.logContainer.leadingAnchor().constraintEqualToAnchor_(self.leadingAnchor()),
            self.logContainer.trailingAnchor().constraintEqualToAnchor_(self.trailingAnchor()),
            self.logContainer.topAnchor().constraintEqualToAnchor_(self.topAnchor()),
            self.logContainer.bottomAnchor().constraintEqualToAnchor_(self.bottomAnchor()),

            self.logScroll.leadingAnchor().constraintEqualToAnchor_(logContent.leadingAnchor()),
            self.logScroll.trailingAnchor().constraintEqualToAnchor_(logContent.trailingAnchor()),
            self.logScroll.topAnchor().constraintEqualToAnchor_(logContent.topAnchor()),
            self.logScroll.bottomAnchor().constraintEqualToAnchor_(logContent.bottomAnchor()),
        ])

        return self

    def viewDidLayout(self):
        objc.super(LogViewer, self).viewDidLayout()
        if self.logText.textContainer() is not None and self.logScroll.contentView() is not None:
            w = self.logScroll.contentView().bounds().size.width
            self.logText.textContainer().setContainerSize_(NSMakeSize(w, float("inf")))
            self.logText.textContainer().setWidthTracksTextView_(True)

    def appendLog_(self, text):
        self.logText.setString_(text)
        self.logText.scrollRangeToVisible_(NSMakeRange(len(text), 0))
