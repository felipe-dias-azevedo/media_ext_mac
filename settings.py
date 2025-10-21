from Cocoa import (
    NSApp, NSWindow,
    NSView, NSTextField, 
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable, NSWindowStyleMaskResizable, NSBackingStoreBuffered, NSMakeRect,
    NSPopUpButton, NSUserDefaults, NSWindowController, NSLayoutConstraint,
    NSStackView, NSBox, NSLineBorder, NSBoxSeparator,
    NSFont, NSColor, NSLayoutAttributeFirstBaseline, NSLayoutAttributeLeading,
    NSUserInterfaceLayoutOrientationHorizontal, NSUserInterfaceLayoutOrientationVertical,
    NSLayoutConstraintOrientationHorizontal, NSBundle
)
import objc
from sys import argv
from db_path import db_path

NORMALIZATION_KEY = "NormalizationFrequency"    # persisted in UserDefaults
OPTIONS = ["Low", "Medium", "High"]

class SettingsContent(NSView):
    def init(self):
        self = objc.super(SettingsContent, self).initWithFrame_(NSMakeRect(0, 0, 520, 240))
        if self is None: 
            return None

        # --- Header labels ---
        bundle = NSBundle.mainBundle().bundleIdentifier()
        self.titleLabel = NSTextField.labelWithString_(f"Bundle: {bundle}")
        path = db_path("media.db", dev_env="--dev" in argv)
        self.subtitleLabel = NSTextField.labelWithString_(f"DB Path: {path}")

        # --- Separator ---
        self.separator = NSBox.alloc().initWithFrame_(NSMakeRect(0,0,0,1))
        self.separator.setBoxType_(NSBoxSeparator)  # modern hairline separator

        # --- Form row: label + popup ---
        self.label = NSTextField.labelWithString_("Normalization frequency:")

        self.popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(0,0,0,0), False)
        self.popup.addItemsWithTitles_(OPTIONS)
        self.popup.setTarget_(self); self.popup.setAction_("normalizationChanged:")

        # Load saved value or default to "Medium"
        defaults = NSUserDefaults.standardUserDefaults()
        saved = defaults.stringForKey_(NORMALIZATION_KEY) or "Medium"
        if saved in OPTIONS:
            self.popup.selectItemWithTitle_(saved)

        # --- Stack views ---
        # Horizontal row for label + popup (like a SwiftUI HStack)
        self.formRow = NSStackView.alloc().initWithFrame_(NSMakeRect(0,0,0,0))
        self.formRow.setOrientation_(NSUserInterfaceLayoutOrientationHorizontal)
        self.formRow.setAlignment_(NSLayoutAttributeFirstBaseline)  # baseline align label & popup
        self.formRow.setSpacing_(12.0)
        self.formRow.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.formRow.addArrangedSubview_(self.label)
        self.formRow.addArrangedSubview_(self.popup)

        # Vertical container (like a SwiftUI VStack)
        self.vstack = NSStackView.alloc().initWithFrame_(NSMakeRect(0,0,0,0))
        self.vstack.setOrientation_(NSUserInterfaceLayoutOrientationVertical)
        self.vstack.setAlignment_(NSLayoutAttributeLeading)
        self.vstack.setSpacing_(8.0)
        self.vstack.setTranslatesAutoresizingMaskIntoConstraints_(False)

        # Add arranged subviews in order:
        self.vstack.addArrangedSubview_(self.titleLabel)
        self.vstack.addArrangedSubview_(self.subtitleLabel)

        # Add a bit more space before the separator
        self.vstack.setCustomSpacing_afterView_(12.0, self.subtitleLabel)
        self.vstack.addArrangedSubview_(self.separator)
        self.vstack.setCustomSpacing_afterView_(16.0, self.separator)

        self.vstack.addArrangedSubview_(self.formRow)

        # Add to view + constraints
        self.addSubview_(self.vstack)
        # Make subviews use Auto Layout
        for v in (self.titleLabel, self.subtitleLabel, self.separator, self.label, self.popup):
            v.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([
            # Pin the stack to the view with standard insets
            self.vstack.leadingAnchor().constraintEqualToAnchor_constant_(self.leadingAnchor(), 24.0),
            self.vstack.trailingAnchor().constraintEqualToAnchor_constant_(self.trailingAnchor(), -24.0),
            self.vstack.topAnchor().constraintEqualToAnchor_constant_(self.topAnchor(), 24.0),
            self.vstack.bottomAnchor().constraintLessThanOrEqualToAnchor_constant_(self.bottomAnchor(), -24.0),

            # Give the popup a sensible min width
            self.popup.widthAnchor().constraintGreaterThanOrEqualToConstant_(140.0),

            # Make the separator expand horizontally
            self.separator.widthAnchor().constraintEqualToAnchor_(self.vstack.widthAnchor()),
            self.separator.heightAnchor().constraintEqualToConstant_(1.0),
        ])

        # Hugging/compression so the popup doesn't squish the label
        self.label.setContentHuggingPriority_forOrientation_(251, NSLayoutConstraintOrientationHorizontal)
        self.label.setContentCompressionResistancePriority_forOrientation_(751, NSLayoutConstraintOrientationHorizontal)
        self.popup.setContentHuggingPriority_forOrientation_(250, NSLayoutConstraintOrientationHorizontal)

        return self

    # Action: save to defaults
    def normalizationChanged_(self, sender):
        title = sender.titleOfSelectedItem()
        NSUserDefaults.standardUserDefaults().setObject_forKey_(title, NORMALIZATION_KEY)
        NSUserDefaults.standardUserDefaults().synchronize()

class SettingsWindowController(NSWindowController):
    shared = None

    @classmethod
    def sharedController(cls):
        if cls.shared is None:
            cls.shared = cls.alloc().init()
        return cls.shared

    def init(self):
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 400, 200), 
            (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable), 
            NSBackingStoreBuffered, 
            False
        )
        win.setTitle_("Settings")

        content = SettingsContent.alloc().init()
        win.setContentView_(content)
        win.center()

        self = objc.super(SettingsWindowController, self).initWithWindow_(win)

        return self

    def showWindow_(self, sender):
        objc.super(SettingsWindowController, self).showWindow_(sender)
        self.window().makeKeyAndOrderFront_(sender)
        NSApp.activateIgnoringOtherApps_(True)

