import objc
from Cocoa import (
    NSView, NSTextField, NSBox, NSButton, NSImage, NSStackView,
    NSFont, NSColor, NSPasteboard, NSStringPboardType,
    NSMakeSize, NSLayoutConstraint, NSUserInterfaceLayoutOrientationHorizontal,
    NSBoxCustom, NSMomentaryPushInButton, NSImageOnly, NSFocusRingTypeNone,
    NSBezelStyleShadowlessSquare, NSFontWeightSemibold, NSMutableAttributedString,
)
from AppKit import (
    NSBeep,
)


class URLRowView(NSView):

    def initWithTarget_action_(self, target, action):
        self = objc.super(URLRowView, self).init()
        if self is None:
            return None

        self.setTranslatesAutoresizingMaskIntoConstraints_(False)

        # URL container (box) — dynamic colors, rounded, border
        self.urlContainer = NSBox.alloc().init()
        self.urlContainer.setBoxType_(NSBoxCustom)
        self.urlContainer.setCornerRadius_(6.0)
        self.urlContainer.setBorderWidth_(1.0)
        self.urlContainer.setBorderColor_(NSColor.separatorColor())
        self.urlContainer.setFillColor_(NSColor.tertiarySystemFillColor())
        self.urlContainer.setContentViewMargins_(NSMakeSize(0.0, 0.0))
        self.urlContainer.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.urlInlineLabel = NSTextField.labelWithString_("URL")
        self.urlInlineLabel.setFont_(NSFont.systemFontOfSize_(NSFont.systemFontSize()))
        self.urlInlineLabel.setTextColor_(NSColor.labelColor())

        self.urlField = NSTextField.alloc().init()
        self.urlField.setBordered_(False)
        self.urlField.setDrawsBackground_(False)
        self.urlField.setFocusRingType_(NSFocusRingTypeNone)
        self.urlField.setPlaceholderString_("https")
        self.urlField.cell().setWraps_(False)
        self.urlField.cell().setScrollable_(True)
        self.urlField.cell().setUsesSingleLineMode_(True)
        self.urlField.setMaximumNumberOfLines_(1)
        self.urlField.setDelegate_(self)
        self.urlField.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.pasteButton = NSButton.alloc().init()
        self.pasteButton.setBordered_(False)
        self.pasteButton.setBezelStyle_(NSBezelStyleShadowlessSquare)
        self.pasteButton.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("doc.on.clipboard", "Paste"))
        self.pasteButton.setImagePosition_(NSImageOnly)
        self.pasteButton.setButtonType_(NSMomentaryPushInButton)
        self.pasteButton.setToolTip_("Paste")
        self.pasteButton.setTarget_(self)
        self.pasteButton.setAction_("pasteURL:")
        self.pasteButton.setTranslatesAutoresizingMaskIntoConstraints_(False)

        urlRow = NSStackView.stackViewWithViews_([
            self.urlInlineLabel,
            self.urlField,
            self.pasteButton,
        ])
        urlRow.setOrientation_(NSUserInterfaceLayoutOrientationHorizontal)
        urlRow.setSpacing_(10.0)
        urlRow.setTranslatesAutoresizingMaskIntoConstraints_(False)

        urlContent = self.urlContainer.contentView()
        urlContent.addSubview_(urlRow)

        # Extract button + pill
        self.extractButtonBox = NSBox.alloc().init()
        self.extractButtonBox.setBoxType_(NSBoxCustom)
        self.extractButtonBox.setCornerRadius_(8.0)
        self.extractButtonBox.setBorderWidth_(0.0)
        self.extractButtonBox.setContentViewMargins_(NSMakeSize(0.0, 0.0))
        self.extractButtonBox.setFillColor_(NSColor.systemBlueColor())
        self.extractButtonBox.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.extractButton = NSButton.alloc().init()
        self.extractButton.setTitle_("Extract")
        self.extractButton.setBordered_(False)
        self.extractButton.setBezelStyle_(NSBezelStyleShadowlessSquare)
        self.extractButton.setFont_(NSFont.systemFontOfSize_weight_(NSFont.systemFontSize(), NSFontWeightSemibold))
        self.extractButton.setContentTintColor_(NSColor.whiteColor())
        attr = NSMutableAttributedString.alloc().initWithString_("Extract")
        self.extractButton.setAttributedTitle_(attr)
        self.extractButton.setTarget_(target)
        self.extractButton.setAction_(action)
        self.extractButton.setTranslatesAutoresizingMaskIntoConstraints_(False)

        extractContent = self.extractButtonBox.contentView()
        extractContent.addSubview_(self.extractButton)

        self.addSubview_(self.urlContainer)
        self.addSubview_(self.extractButtonBox)

        for view in (self.urlContainer, self.extractButtonBox, self.extractButton, self.urlInlineLabel, self.urlField, self.pasteButton):
            view.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([
            self.urlContainer.leadingAnchor().constraintEqualToAnchor_(self.leadingAnchor()),
            self.urlContainer.topAnchor().constraintEqualToAnchor_(self.topAnchor()),
            self.urlContainer.bottomAnchor().constraintEqualToAnchor_(self.bottomAnchor()),
            self.urlContainer.trailingAnchor().constraintEqualToAnchor_constant_(self.extractButtonBox.leadingAnchor(), -12.0),
            self.urlContainer.heightAnchor().constraintEqualToConstant_(32.0),

            urlRow.leadingAnchor().constraintEqualToAnchor_constant_(urlContent.leadingAnchor(), 10.0),
            urlRow.trailingAnchor().constraintEqualToAnchor_constant_(urlContent.trailingAnchor(), -10.0),
            urlRow.centerYAnchor().constraintEqualToAnchor_(urlContent.centerYAnchor()),

            self.extractButtonBox.trailingAnchor().constraintEqualToAnchor_(self.trailingAnchor()),
            self.extractButtonBox.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),
            self.extractButtonBox.heightAnchor().constraintEqualToConstant_(32.0),
            self.extractButtonBox.widthAnchor().constraintEqualToConstant_(76.0),

            self.extractButton.centerXAnchor().constraintEqualToAnchor_(extractContent.centerXAnchor()),
            self.extractButton.centerYAnchor().constraintEqualToAnchor_(extractContent.centerYAnchor()),
            self.extractButton.leadingAnchor().constraintGreaterThanOrEqualToAnchor_constant_(extractContent.leadingAnchor(), 8.0),
            self.extractButton.trailingAnchor().constraintLessThanOrEqualToAnchor_constant_(extractContent.trailingAnchor(), -8.0),
        ])

        return self

    def pasteURL_(self, sender):
        pb = NSPasteboard.generalPasteboard()
        s = pb.stringForType_(NSStringPboardType)
        if not s:
            NSBeep()
            return
        self.urlField.setStringValue_(s)
    
    def urlValue(self):
        return self.urlField.stringValue()

    def clearURL(self):
        self.urlField.setStringValue_("")

    def setEnabled_(self, enabled):
        self.urlField.setEnabled_(enabled)
        self.pasteButton.setEnabled_(enabled)
        self.extractButton.setEnabled_(enabled)
