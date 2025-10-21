from Cocoa import (
    NSApp, NSWindow,
    NSView, NSTextField, 
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable, NSWindowStyleMaskResizable, NSBackingStoreBuffered, NSMakeRect,
    NSPopUpButton, NSUserDefaults, NSWindowController, NSLayoutConstraint
)
import objc

NORMALIZATION_KEY = "NormalizationFrequency"    # persisted in UserDefaults
OPTIONS = ["Low", "Medium", "High"]

class SettingsContent(NSView):
    def init(self):
        self = objc.super(SettingsContent, self).initWithFrame_(NSMakeRect(0, 0, 520, 200))
        if self is None: return None
        self.setWantsLayer_(True)

        # Label
        self.label = NSTextField.alloc().initWithFrame_(NSMakeRect(0,0,0,0))
        self.label.setStringValue_("Normalization frequency:")
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)

        # Pop-up (like Picker(.menu))
        self.popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(NSMakeRect(0,0,0,0), False)
        self.popup.addItemsWithTitles_(OPTIONS)
        self.popup.setTarget_(self)
        self.popup.setAction_("normalizationChanged:")

        # Load saved value or default to "Medium"
        defaults = NSUserDefaults.standardUserDefaults()
        saved = defaults.stringForKey_(NORMALIZATION_KEY) or "Medium"
        if saved in OPTIONS:
            self.popup.selectItemWithTitle_(saved)

        # Auto Layout
        for v in (self.label, self.popup):
            v.setTranslatesAutoresizingMaskIntoConstraints_(False)
            self.addSubview_(v)

        # Constraints (use NSLayoutConstraint.activateConstraints_ and correct anchor methods)
        NSLayoutConstraint.activateConstraints_([
            self.label.leadingAnchor().constraintEqualToAnchor_constant_(self.leadingAnchor(), 24.0),
            self.label.topAnchor().constraintEqualToAnchor_constant_(self.topAnchor(), 36.0),

            self.popup.leadingAnchor().constraintEqualToAnchor_constant_(self.label.trailingAnchor(), 12.0),
            self.popup.centerYAnchor().constraintEqualToAnchor_(self.label.centerYAnchor()),
            self.popup.widthAnchor().constraintGreaterThanOrEqualToConstant_(140.0),
        ])

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
        # initialize the NSWindowController with the window instance directly on super
        mask = (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
                NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable)

        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 400, 200), mask, NSBackingStoreBuffered, False
        )
        win.setTitle_("Settings")

        content = SettingsContent.alloc().init()
        win.setContentView_(content)
        win.center()

        # call initWithWindow_ on super to correctly initialize the controller
        self = objc.super(SettingsWindowController, self).initWithWindow_(win)

        return self

    def showWindow_(self, sender):
        objc.super(SettingsWindowController, self).showWindow_(sender)
        self.window().makeKeyAndOrderFront_(sender)
        NSApp.activateIgnoringOtherApps_(True)

