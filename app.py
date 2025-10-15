from Cocoa import (
    NSObject, NSApplication, NSApp, NSWindow, NSMenu, NSMenuItem,
    NSView, NSViewController, NSScrollView, NSTextView, NSTextField, NSTableCellView,
    NSButton, NSImage, NSBox, NSStackView, NSProgressIndicator,
    NSSplitViewController, NSSplitViewItem, NSToolbar, NSImageView,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSTableViewStyleInset,
    NSWindowStyleMaskMiniaturizable, NSWindowStyleMaskResizable, NSBackingStoreBuffered,
    NSApplicationActivationPolicyRegular, NSFont, NSColor, NSPasteboard,
    NSStringPboardType, NSLayoutConstraint, NSLayoutConstraintOrientationHorizontal,
    NSMutableAttributedString, NSSize, NSRect, NSMakeSize, NSMakeRect, NSMakeRange,
    NSUserInterfaceLayoutOrientationHorizontal, NSBoxCustom, NSMomentaryPushInButton, NSControlSizeLarge,
    NSBezelStyleShadowlessSquare, NSImageOnly, NSFocusRingTypeNone, NSBezelStyleRounded, NSProgressIndicatorStyleSpinning,
    NSTextLayoutOrientationHorizontal, NSLineBreakByTruncatingMiddle, NSFontWeightMedium
)
from AppKit import (
    NSTableView, NSTableColumn, NSImageSymbolConfiguration
)
import AppKit as AK
from Foundation import NSTimer
import objc


# -----------------------------
# Models
# -----------------------------

class MediaItem(object):
    __slots__ = ("title", "timestamp", "isGroup")
    def __init__(self, title="", timestamp="", isGroup=False):
        self.title = title
        self.timestamp = timestamp
        self.isGroup = isGroup

    @classmethod
    def group(cls, groupTitle):
        return cls(title=groupTitle, timestamp="", isGroup=True)

    @classmethod
    def item(cls, title, timestamp):
        return cls(title=title, timestamp=timestamp, isGroup=False)


# -----------------------------
# Sidebar VC
# -----------------------------

class SidebarVC(NSViewController, protocols=[objc.protocolNamed("NSTableViewDataSource"),
                                             objc.protocolNamed("NSTableViewDelegate")]):
    def init(self):
        self = objc.super(SidebarVC, self).init()
        if self is None:
            return None
        self.table = NSTableView.alloc().init()
        self.scroll = NSScrollView.alloc().init()
        self.data = [
            MediaItem.group("January"),
            MediaItem.item("o-astronauta-de-marmore.mp3", "13/10/25, 16:24:20"),
            MediaItem.item("voce-nao-me-ensinou-a-te-esquecer.mp3", "13/10/25, 16:24:20"),
            MediaItem.item("test.mp3", "13/10/25, 16:24:36"),
            MediaItem.item("test.mp3", "13/10/25, 16:25:21"),
        ]
        return self

    def loadView(self):
        self.setView_(NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 300, 400)))

        self.scroll.setDocumentView_(self.table)
        self.scroll.setHasVerticalScroller_(True)
        self.table.setHeaderView_(None)
        self.table.setRowHeight_(48.0)
        self.table.setIntercellSpacing_(NSMakeSize(0.0, 0.0))
        self.table.setStyle_(NSTableViewStyleInset)
        self.table.setBackgroundColor_(NSColor.windowBackgroundColor())

        col = NSTableColumn.alloc().initWithIdentifier_("main")
        self.table.addTableColumn_(col)
        self.table.setDelegate_(self)
        self.table.setDataSource_(self)

        self.view().addSubview_(self.scroll)
        self.scroll.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([
            self.scroll.leadingAnchor().constraintEqualToAnchor_(self.view().leadingAnchor()),
            self.scroll.trailingAnchor().constraintEqualToAnchor_(self.view().trailingAnchor()),
            self.scroll.topAnchor().constraintEqualToAnchor_(self.view().topAnchor()),
            self.scroll.bottomAnchor().constraintEqualToAnchor_(self.view().bottomAnchor()),
        ])

    # Data source
    def numberOfRowsInTableView_(self, tableView):
        return len(self.data)

    # Group rows
    def tableView_isGroupRow_(self, tableView, row):
        return bool(self.data[row].isGroup)

    # Views per row
    def tableView_viewForTableColumn_row_(self, tableView, tableColumn, row):
        item = self.data[row]
        v = NSTableCellView.alloc().init()
        if item.isGroup:
            label = NSTextField.labelWithString_(item.title)
            label.setFont_(NSFont.boldSystemFontOfSize_(NSFont.systemFontSize()))
            label.setTextColor_(NSColor.secondaryLabelColor())
            v.addSubview_(label)
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)
            NSLayoutConstraint.activateConstraints_([
                label.leadingAnchor().constraintEqualToAnchor_constant_(v.leadingAnchor(), 12.0),
                label.centerYAnchor().constraintEqualToAnchor_(v.centerYAnchor())
            ])
            return v
        else:
            title = NSTextField.labelWithString_(item.title)
            title.setFont_(NSFont.systemFontOfSize_(12.0))
            title.setLineBreakMode_(NSLineBreakByTruncatingMiddle)  # byTruncatingMiddle

            sub = NSTextField.labelWithString_(item.timestamp)
            sub.setFont_(NSFont.systemFontOfSize_(10.0))
            sub.setTextColor_(NSColor.secondaryLabelColor())

            v.addSubview_(title)
            v.addSubview_(sub)
            title.setTranslatesAutoresizingMaskIntoConstraints_(False)
            sub.setTranslatesAutoresizingMaskIntoConstraints_(False)
            NSLayoutConstraint.activateConstraints_([
                title.leadingAnchor().constraintEqualToAnchor_constant_(v.leadingAnchor(), 12.0),
                title.trailingAnchor().constraintEqualToAnchor_constant_(v.trailingAnchor(), -12.0),
                title.topAnchor().constraintEqualToAnchor_constant_(v.topAnchor(), 6.0),
                sub.leadingAnchor().constraintEqualToAnchor_(title.leadingAnchor()),
                sub.trailingAnchor().constraintEqualToAnchor_(title.trailingAnchor()),
                sub.topAnchor().constraintEqualToAnchor_constant_(title.bottomAnchor(), 0.0),
                sub.bottomAnchor().constraintEqualToAnchor_constant_(v.bottomAnchor(), -6.0),
            ])
            return v


# -----------------------------
# Status Pill
# -----------------------------

class StatusPill(NSView):
    KindSuccess = 0
    KindProgress = 1

    def init(self):
        self = objc.super(StatusPill, self).init()
        if self is None:
            return None

        self.box = NSBox.alloc().init()
        self.icon = NSImageView.alloc().init()
        self.spinner = NSProgressIndicator.alloc().init()
        self.label = NSTextField.labelWithString_("")

        self.box.setBoxType_(NSBoxCustom)
        self.box.setCornerRadius_(8.0)
        self.box.setBorderWidth_(0.5)
        self.box.setBorderColor_(NSColor.separatorColor())
        self.box.setFillColor_(NSColor.controlBackgroundColor())
        self.addSubview_(self.box)

        conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_(14.0, 2)
        self.icon.setSymbolConfiguration_(conf)
        img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("checkmark", None)
        self.icon.setContentTintColor_(NSColor.systemGreenColor())
        self.icon.setImage_(img)

        self.spinner.setStyle_(NSProgressIndicatorStyleSpinning)  # NSProgressIndicatorStyleSpinning
        self.spinner.setControlSize_(1)  # small
        self.spinner.setDisplayedWhenStopped_(False)
        self.label.setFont_(NSFont.systemFontOfSize_weight_(13.0, NSFontWeightMedium))

        stack = NSStackView.stackViewWithViews_([self.icon, self.spinner, self.label])
        stack.setOrientation_(NSUserInterfaceLayoutOrientationHorizontal)
        stack.setSpacing_(8.0)
        # stack.setAlignment_(NSStackViewAlignmentCenterY)
        self.addSubview_(stack)
        self.stack = stack

        for sub in (self.box, stack):
            sub.setTranslatesAutoresizingMaskIntoConstraints_(False)
        NSLayoutConstraint.activateConstraints_([
            self.box.leadingAnchor().constraintEqualToAnchor_(self.leadingAnchor()),
            self.box.trailingAnchor().constraintEqualToAnchor_(self.trailingAnchor()),
            self.box.topAnchor().constraintEqualToAnchor_(self.topAnchor()),
            self.box.bottomAnchor().constraintEqualToAnchor_(self.bottomAnchor()),

            stack.leadingAnchor().constraintEqualToAnchor_constant_(self.leadingAnchor(), 16.0),
            stack.trailingAnchor().constraintLessThanOrEqualToAnchor_constant_(self.trailingAnchor(), -16.0),
            stack.topAnchor().constraintEqualToAnchor_constant_(self.topAnchor(), 8.0),
            stack.bottomAnchor().constraintEqualToAnchor_constant_(self.bottomAnchor(), -8.0),
        ])
        self.setKind_message_(self.KindSuccess, "Success")
        return self

    def setKind_message_(self, kind, msg):
        if kind == self.KindSuccess:
            self.spinner.stopAnimation_(None)
            self.spinner.setHidden_(True)
            self.icon.setHidden_(False)
            self.label.setStringValue_(msg)
            self.label.setTextColor_(NSColor.systemGreenColor())
        else:
            self.icon.setHidden_(True)
            self.spinner.setHidden_(False)
            self.spinner.startAnimation_(None)
            self.label.setStringValue_(msg)
            self.label.setTextColor_(NSColor.labelColor())


# -----------------------------
# Content VC (right side)
# -----------------------------

class ContentVC(NSViewController):
    def init(self):
        self = objc.super(ContentVC, self).init()
        if self is None:
            return None
        self.urlContainer = NSView.alloc().init()
        self.urlInlineLabel = NSTextField.labelWithString_("URL")
        self.urlField = NSTextField.alloc().init()
        self.pasteButton = NSButton.alloc().init()
        self.extractButton = NSButton.alloc().init()
        self.statusPill = StatusPill.alloc().init()

        # self.logScroll = NSScrollView.alloc().init()
        # self.logText = NSTextView.alloc().init()
        # self.logScroll.setDocumentView_(self.logText)
        self.logScroll = NSTextView.scrollablePlainDocumentContentTextView()
        self.logScroll.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.logText = self.logScroll.documentView()  # type: NSTextView

        return self

    def viewDidAppear(self):
        objc.super(ContentVC, self).viewDidAppear()
        self.extractButton.setKeyEquivalent_("\r")
        if self.view().window() is not None:
            self.view().window().setDefaultButtonCell_(self.extractButton.cell())

    def loadView(self):
        self.setView_(NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 400)))

        # URL container look
        self.urlContainer.setWantsLayer_(True)
        if self.urlContainer.layer() is None:
            # force layer creation on some older builds
            self.view().setWantsLayer_(True)
            self.urlContainer.setWantsLayer_(True)
        if self.urlContainer.layer() is not None:
            self.urlContainer.layer().setCornerRadius_(8.0)
            self.urlContainer.layer().setBorderWidth_(0.5)
            self.urlContainer.layer().setBorderColor_(NSColor.separatorColor().CGColor())
            self.urlContainer.layer().setBackgroundColor_(NSColor.controlBackgroundColor().CGColor())

        self.urlInlineLabel.setFont_(NSFont.systemFontOfSize_(12.0))
        self.urlInlineLabel.setTextColor_(NSColor.secondaryLabelColor())

        # URL field
        self.urlField.setBordered_(False)
        self.urlField.setDrawsBackground_(False)
        self.urlField.setFocusRingType_(NSFocusRingTypeNone)  # none
        self.urlField.setPlaceholderString_("https")
        self.urlField.cell().setWraps_(False)
        self.urlField.cell().setScrollable_(True)
        self.urlField.cell().setUsesSingleLineMode_(True)
        self.urlField.setMaximumNumberOfLines_(1)

        # Paste button
        self.pasteButton.setBordered_(False)
        self.pasteButton.setBezelStyle_(NSBezelStyleShadowlessSquare)  # shadowlessSquare
        self.pasteButton.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("doc.on.clipboard", "Paste"))
        self.pasteButton.setImagePosition_(NSImageOnly)  # imageOnly
        self.pasteButton.setButtonType_(NSMomentaryPushInButton)  # momentaryPushIn
        self.pasteButton.setToolTip_("Paste")

        # Extract button
        self.extractButton.setTitle_("Extract")
        self.extractButton.setBordered_(True)
        self.extractButton.setBezelStyle_(NSBezelStyleRounded)
        self.extractButton.setButtonType_(NSMomentaryPushInButton)
        self.extractButton.setToolTip_("Extract")
        self.extractButton.setControlSize_(NSControlSizeLarge)

        attr = NSMutableAttributedString.alloc().initWithString_("Extract")
        self.extractButton.setAttributedTitle_(attr)
        self.extractButton.setContentHuggingPriority_forOrientation_(1000, NSLayoutConstraintOrientationHorizontal)
        self.extractButton.setContentCompressionResistancePriority_forOrientation_(1000, NSLayoutConstraintOrientationHorizontal)

        
        self.logText.setEditable_(False)
        self.logText.setSelectable_(True)
        self.logText.setRichText_(False)
        self.logText.setLayoutOrientation_(NSTextLayoutOrientationHorizontal)
        self.logText.setFont_(NSFont.userFixedPitchFontOfSize_(13.0))
        self.logText.setTextColor_(NSColor.labelColor())
        self.logText.setDrawsBackground_(False)
        self.logText.setTextContainerInset_(NSMakeSize(10.0, 10.0))
        if self.logText.textContainer() is not None:
            # Width tracks the scroll view, infinite height
            self.logText.textContainer().setWidthTracksTextView_(True)
            # We don't know scroll width yet; set 0 here and update later in viewDidLayout
            self.logText.textContainer().setContainerSize_(NSMakeSize(0.0, float("inf")))
        self.logText.setString_("test")

        self.logScroll.setHasVerticalScroller_(True)
        self.logScroll.setBorderType_(0)
        self.logScroll.setDrawsBackground_(False)

        # Logs container with rounded border
        self.logContainer = NSView.alloc().init()
        self.logContainer.setWantsLayer_(True)
        if self.logContainer.layer() is None:
            self.view().setWantsLayer_(True)
            self.logContainer.setWantsLayer_(True)
        if self.logContainer.layer() is not None:
            self.logContainer.layer().setCornerRadius_(8.0)
            self.logContainer.layer().setBorderWidth_(0.5)
            self.logContainer.layer().setBorderColor_(NSColor.separatorColor().CGColor())
            self.logContainer.layer().setBackgroundColor_(NSColor.controlBackgroundColor().CGColor())
        self.logContainer.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.logContainer.addSubview_(self.logScroll)

        # Add subviews (outer)
        for sub in (self.urlContainer, self.extractButton, self.statusPill, self.logContainer):
            sub.setTranslatesAutoresizingMaskIntoConstraints_(False)
            self.view().addSubview_(sub)

        # Add URL inner
        for sub in (self.urlInlineLabel, self.urlField, self.pasteButton):
            sub.setTranslatesAutoresizingMaskIntoConstraints_(False)
            self.urlContainer.addSubview_(sub)

        # Constraints
        NSLayoutConstraint.activateConstraints_([
            self.urlContainer.leadingAnchor().constraintEqualToAnchor_constant_(self.view().leadingAnchor(), 24.0),
            self.urlContainer.topAnchor().constraintEqualToAnchor_constant_(self.view().topAnchor(), 16.0),
            self.urlContainer.trailingAnchor().constraintEqualToAnchor_constant_(self.extractButton.leadingAnchor(), -12.0),
            self.urlContainer.heightAnchor().constraintEqualToConstant_(30.0),

            self.urlInlineLabel.leadingAnchor().constraintEqualToAnchor_constant_(self.urlContainer.leadingAnchor(), 10.0),
            self.urlInlineLabel.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),

            self.urlField.leadingAnchor().constraintEqualToAnchor_constant_(self.urlInlineLabel.trailingAnchor(), 10.0),
            self.urlField.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),
            self.urlField.trailingAnchor().constraintEqualToAnchor_constant_(self.pasteButton.leadingAnchor(), -8.0),

            self.pasteButton.trailingAnchor().constraintEqualToAnchor_constant_(self.urlContainer.trailingAnchor(), -10.0),
            self.pasteButton.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),

            self.extractButton.trailingAnchor().constraintEqualToAnchor_constant_(self.view().trailingAnchor(), -24.0),
            self.extractButton.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),
            self.extractButton.heightAnchor().constraintEqualToConstant_(22.0),

            self.statusPill.leadingAnchor().constraintEqualToAnchor_(self.urlContainer.leadingAnchor()),
            self.statusPill.trailingAnchor().constraintEqualToAnchor_(self.extractButton.trailingAnchor()),
            self.statusPill.topAnchor().constraintEqualToAnchor_constant_(self.urlContainer.bottomAnchor(), 12.0),
            self.statusPill.heightAnchor().constraintGreaterThanOrEqualToConstant_(32.0),

            self.logContainer.leadingAnchor().constraintEqualToAnchor_(self.statusPill.leadingAnchor()),
            self.logContainer.trailingAnchor().constraintEqualToAnchor_(self.statusPill.trailingAnchor()),
            self.logContainer.topAnchor().constraintEqualToAnchor_constant_(self.statusPill.bottomAnchor(), 12.0),
            self.logContainer.bottomAnchor().constraintEqualToAnchor_constant_(self.view().bottomAnchor(), -20.0),

            self.logScroll.leadingAnchor().constraintEqualToAnchor_(self.logContainer.leadingAnchor()),
            self.logScroll.trailingAnchor().constraintEqualToAnchor_(self.logContainer.trailingAnchor()),
            self.logScroll.topAnchor().constraintEqualToAnchor_(self.logContainer.topAnchor()),
            self.logScroll.bottomAnchor().constraintEqualToAnchor_(self.logContainer.bottomAnchor()),
        ])

        # Actions
        self.pasteButton.setTarget_(self)
        self.pasteButton.setAction_("pasteURL:")
        self.extractButton.setTarget_(self)
        self.extractButton.setAction_("extract:")

    def viewDidLayout(self):
        objc.super(ContentVC, self).viewDidLayout()
        # Keep wrapping width synced
        if self.logText.textContainer() is not None and self.logScroll.contentView() is not None:
            w = self.logScroll.contentView().bounds().size.width
            self.logText.textContainer().setContainerSize_(NSMakeSize(w, float("inf")))
            self.logText.textContainer().setWidthTracksTextView_(True)

    # pasteURL: action
    def pasteURL_(self, sender):
        pb = NSPasteboard.generalPasteboard()
        s = pb.stringForType_(NSStringPboardType)
        if s:
            self.urlField.setStringValue_(s)
        self.statusPill.setKind_message_(StatusPill.KindSuccess, "Success")

    def appendLog_(self, text):
        current = self.logText.string() or ""
        if current:
            current = current + "\n" + text
        else:
            current = text
        self.logText.setString_(current)
        self.logText.scrollRangeToVisible_(NSMakeRange(len(current), 0))


    def _finishExtract_(self, timer):
        self.statusPill.setKind_message_(StatusPill.KindSuccess, "Success")
        self.appendLog_("test 2\ntest 3")

    def extract_(self, sender):
        self.statusPill.setKind_message_(StatusPill.KindProgress, "Downloading")
        self.appendLog_("test 1")
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1.2, self, "_finishExtract:", None, False)


# -----------------------------
# Split container
# -----------------------------

class RootSplitVC(NSSplitViewController):
    def viewDidLoad(self):
        objc.super(RootSplitVC, self).viewDidLoad()
        leftVC = SidebarVC.alloc().init()
        rightVC = ContentVC.alloc().init()
        left = NSSplitViewItem.splitViewItemWithViewController_(leftVC)
        right = NSSplitViewItem.splitViewItemWithViewController_(rightVC)
        left.setCanCollapse_(False)
        self.addSplitViewItem_(left)
        self.addSplitViewItem_(right)


# -----------------------------
# App Delegate + Menus
# -----------------------------

class AppDelegate(NSObject):
    window = objc.ivar()

    def applicationDidFinishLaunching_(self, notification):
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        self.buildMenus()

        splitVC = RootSplitVC.alloc().init()
        rect = NSMakeRect(0, 0, 720, 480)
        style = (NSWindowStyleMaskTitled |
                 NSWindowStyleMaskClosable |
                 NSWindowStyleMaskMiniaturizable |
                 NSWindowStyleMaskResizable)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.window.center()
        self.window.setTitle_("Media.Ext")
        self.window.setContentViewController_(splitVC)
        self.window.makeKeyAndOrderFront_(None)
        self.window.setContentMinSize_(NSMakeSize(600, 360))

        toolbar = NSToolbar.alloc().initWithIdentifier_("MainToolbar")
        toolbar.setAllowsUserCustomization_(False)
        self.window.setToolbar_(toolbar)

        NSApp.activateIgnoringOtherApps_(True)

    def applicationShouldHandleReopen_hasVisibleWindows_(self, app, flag):
        if not flag and self.window is not None:
            self.window.makeKeyAndOrderFront_(None)
        return True

    # Menus
    def buildMenus(self):
        main = NSMenu.alloc().init()

        # App
        appItem = NSMenuItem.alloc().init()
        appMenu = NSMenu.alloc().init()
        about = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("About MediaExtSwiftUI",
                                                                       objc.selector(NSApp.orderFrontStandardAboutPanel_, signature=b"v@:@"),
                                                                       "")
        about.setTarget_(NSApp)
        appMenu.addItem_(about)
        appMenu.addItem_(NSMenuItem.separatorItem())
        appMenu.addItemWithTitle_action_keyEquivalent_("Preferences…", None, ",")
        appMenu.addItem_(NSMenuItem.separatorItem())
        appMenu.addItemWithTitle_action_keyEquivalent_("Quit MediaExtSwiftUI",
                                                       objc.selector(NSApp.terminate_, signature=b"v@:@"),
                                                       "q")
        appItem.setSubmenu_(appMenu)
        main.addItem_(appItem)

        # File
        fileItem = NSMenuItem.alloc().init()
        fileMenu = NSMenu.alloc().initWithTitle_("File")
        fileMenu.addItemWithTitle_action_keyEquivalent_("Close Window",
                                                        objc.selector(NSWindow.performClose_, signature=b"v@:@"),
                                                        "w")
        fileItem.setSubmenu_(fileMenu)
        main.addItem_(fileItem)

        # Edit
        editItem = NSMenuItem.alloc().init()
        editMenu = NSMenu.alloc().initWithTitle_("Edit")
        editMenu.addItemWithTitle_action_keyEquivalent_("Cut", objc.selector(NSTextView.cut_, signature=b"v@:@"), "x")
        editMenu.addItemWithTitle_action_keyEquivalent_("Copy", objc.selector(NSTextView.copy_, signature=b"v@:@"), "c")
        editMenu.addItemWithTitle_action_keyEquivalent_("Paste", objc.selector(NSTextView.paste_, signature=b"v@:@"), "v")
        editMenu.addItemWithTitle_action_keyEquivalent_("Select All", objc.selector(NSTextView.selectAll_, signature=b"v@:@"), "a")
        editItem.setSubmenu_(editMenu)
        main.addItem_(editItem)

        # Window
        winItem = NSMenuItem.alloc().init()
        winMenu = NSMenu.alloc().initWithTitle_("Window")
        winMenu.addItemWithTitle_action_keyEquivalent_("Minimize", objc.selector(NSWindow.performMiniaturize_, signature=b"v@:@"), "m")
        winMenu.addItemWithTitle_action_keyEquivalent_("Zoom", objc.selector(NSWindow.performZoom_, signature=b"v@:@"), "")
        winMenu.addItem_(NSMenuItem.separatorItem())
        winMenu.addItemWithTitle_action_keyEquivalent_("Bring All to Front", objc.selector(NSApplication.arrangeInFront_, signature=b"v@:@"), "")
        winItem.setSubmenu_(winMenu)
        main.addItem_(winItem)
        NSApp.setWindowsMenu_(winMenu)

        # Help
        helpItem = NSMenuItem.alloc().init()
        helpMenu = NSMenu.alloc().initWithTitle_("Help")
        helpMenu.addItemWithTitle_action_keyEquivalent_("MediaExtSwiftUI Help", None, "?")
        helpItem.setSubmenu_(helpMenu)
        main.addItem_(helpItem)

        NSApp.setMainMenu_(main)


def main():
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
