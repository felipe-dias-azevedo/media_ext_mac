# pip install pyobjc
import uuid
from datetime import datetime, timedelta

import objc
from Cocoa import (
    NSApp, NSApplication, NSApplicationActivationPolicyRegular,
    NSObject, NSWindow, NSView, NSMenu, NSMenuItem, NSProcessInfo,
    NSSplitViewController, NSSplitViewItem,
    NSVisualEffectView, NSVisualEffectMaterialSidebar,
    NSVisualEffectStateFollowsWindowActiveState, NSVisualEffectBlendingModeBehindWindow,
    NSTableView, NSTableColumn, NSScrollView, NSTextField,
    NSWindowController, NSToolbar, NSToolbarItem,
    NSToolbarFlexibleSpaceItemIdentifier, NSToolbarToggleSidebarItemIdentifier,
    NSProgressIndicator, NSControlSizeSmall,
    NSLayoutConstraint, NSFont, NSColor
)
from AppKit import NSFontWeightSemibold, NSToolbarDisplayModeIconOnly
from Foundation import NSDateFormatter, NSTimer


# --------------------------
# Models / Helpers
# --------------------------

class HistoryItem:
    def __init__(self, id_: uuid.UUID, date: datetime):
        self.id = id_
        self.date = date


class DateHelper:
    formatter = NSDateFormatter.alloc().init()
    formatter.setLocale_(objc.lookUpClass("NSLocale").currentLocale())
    formatter.setDateStyle_(2)  # .medium
    formatter.setTimeStyle_(1)  # .short

    @staticmethod
    def to_string(py_dt: datetime) -> str:
        nsdate = objc.lookUpClass("NSDate").dateWithTimeIntervalSince1970_(py_dt.timestamp())
        return str(DateHelper.formatter.stringFromDate_(nsdate))


# --------------------------
# Media Manager (with KVO)
# --------------------------

class MediaManager(NSObject):
    def init(self):
        self = objc.super(MediaManager, self).init()
        if self is None:
            return None
        self._isLoading = True
        return self

    def isLoading(self):
        return self._isLoading

    def setIsLoading_(self, value):
        self.willChangeValueForKey_("isLoading")
        self._isLoading = bool(value)
        self.didChangeValueForKey_("isLoading")


# --------------------------
# Detail ("HomeView" equivalent)
# --------------------------

class DetailViewController(objc.lookUpClass("NSViewController")):
    def loadView(self):
        container = NSView.alloc().init()

        pad = NSView.alloc().init()
        pad.setTranslatesAutoresizingMaskIntoConstraints_(False)
        container.addSubview_(pad)

        self.label = NSTextField.labelWithString_("HomeView")
        self.label.setFont_(NSFont.systemFontOfSize_weight_(20.0, NSFontWeightSemibold))  # semibold
        self.label.setTranslatesAutoresizingMaskIntoConstraints_(False)
        pad.addSubview_(self.label)

        # Constraints using anchors
        NSLayoutConstraint.activateConstraints_([
            pad.leadingAnchor().constraintEqualToAnchor_constant_(container.leadingAnchor(), 16),
            pad.trailingAnchor().constraintEqualToAnchor_constant_(container.trailingAnchor(), -16),
            pad.topAnchor().constraintEqualToAnchor_constant_(container.topAnchor(), 16),
            pad.bottomAnchor().constraintGreaterThanOrEqualToAnchor_constant_(container.bottomAnchor(), -16),

            self.label.leadingAnchor().constraintEqualToAnchor_(pad.leadingAnchor()),
            self.label.topAnchor().constraintEqualToAnchor_(pad.topAnchor()),
        ])

        self.setView_(container)  # <-- IMPORTANT

    def updateWithItem_(self, item):
        if item is None:
            self.label.setStringValue_("HomeView")
        else:
            self.label.setStringValue_(f"Selected: {DateHelper.to_string(item.date)}")


# --------------------------
# Sidebar (blur + list)
# --------------------------

class SidebarViewController(objc.lookUpClass("NSViewController")):
    def initWithHistory_(self, history):
        self = objc.super(SidebarViewController, self).initWithNibName_bundle_(None, None)
        if self is None:
            return None
        self.history = history
        self.onSelectionChange = None
        return self

    def loadView(self):
        container = NSView.alloc().init()

        blur = NSVisualEffectView.alloc().init()
        blur.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        blur.setState_(NSVisualEffectStateFollowsWindowActiveState)
        blur.setMaterial_(NSVisualEffectMaterialSidebar)
        blur.setTranslatesAutoresizingMaskIntoConstraints_(False)
        container.addSubview_(blur)

        self.table = NSTableView.alloc().init()
        self.table.setHeaderView_(None)
        self.table.setRowHeight_(24)
        self.table.setIntercellSpacing_((6, 6))
        self.table.setBackgroundColor_(NSColor.clearColor())
        self.table.setDelegate_(self)
        self.table.setDataSource_(self)

        col = NSTableColumn.alloc().initWithIdentifier_("date")
        col.setTitle_("History")
        self.table.addTableColumn_(col)

        scroll = NSScrollView.alloc().init()
        scroll.setDocumentView_(self.table)
        scroll.setHasVerticalScroller_(True)
        scroll.setDrawsBackground_(False)
        scroll.setTranslatesAutoresizingMaskIntoConstraints_(False)
        container.addSubview_(scroll)

        NSLayoutConstraint.activateConstraints_([
            blur.leadingAnchor().constraintEqualToAnchor_(container.leadingAnchor()),
            blur.trailingAnchor().constraintEqualToAnchor_(container.trailingAnchor()),
            blur.topAnchor().constraintEqualToAnchor_(container.topAnchor()),
            blur.bottomAnchor().constraintEqualToAnchor_(container.bottomAnchor()),

            scroll.leadingAnchor().constraintEqualToAnchor_(container.leadingAnchor()),
            scroll.trailingAnchor().constraintEqualToAnchor_(container.trailingAnchor()),
            scroll.topAnchor().constraintEqualToAnchor_(container.topAnchor()),
            scroll.bottomAnchor().constraintEqualToAnchor_(container.bottomAnchor()),
        ])

        self.setView_(container)  # <-- IMPORTANT

    # Data source
    def numberOfRowsInTableView_(self, tableView):
        return len(self.history)

    # Delegate
    def tableView_viewForTableColumn_row_(self, tableView, tableColumn, row):
        cell_id = "cell"
        view = tableView.makeViewWithIdentifier_owner_(cell_id, self)
        if view is None:
            view = objc.lookUpClass("NSTableCellView").alloc().init()
            view.setIdentifier_(cell_id)
            txt = NSTextField.labelWithString_("")
            txt.setLineBreakMode_(0)  # byTruncatingTail
            txt.setTranslatesAutoresizingMaskIntoConstraints_(False)
            view.addSubview_(txt)
            view.setTextField_(txt)
            NSLayoutConstraint.activateConstraints_([
                txt.leadingAnchor().constraintEqualToAnchor_constant_(view.leadingAnchor(), 12),
                txt.trailingAnchor().constraintEqualToAnchor_constant_(view.trailingAnchor(), -12),
                txt.centerYAnchor().constraintEqualToAnchor_(view.centerYAnchor())
            ])
        item = self.history[row]
        view.textField().setStringValue_(DateHelper.to_string(item.date))
        return view

    def tableViewSelectionDidChange_(self, notification):
        idx = self.table.selectedRow()
        item = self.history[idx] if 0 <= idx < len(self.history) else None
        if self.onSelectionChange is not None:
            self.onSelectionChange(item)


# --------------------------
# SplitViewController
# --------------------------

class MainSplitVC(NSSplitViewController):
    def initWithHistory_(self, history):
        self = objc.super(MainSplitVC, self).initWithNibName_bundle_(None, None)
        if self is None:
            return None

        self.sidebarVC = SidebarViewController.alloc().initWithHistory_(history)
        self.detailVC = DetailViewController.alloc().initWithNibName_bundle_(None, None)

        self.sidebarVC.onSelectionChange = lambda item: self.detailVC.updateWithItem_(item)

        # Proper sidebar factory:
        try:
            sidebar_item = NSSplitViewItem.sidebarWithViewController_(self.sidebarVC)
        except Exception:
            # Fallback if sidebarWithViewController_ isn't available on very old SDKs
            sidebar_item = NSSplitViewItem.splitViewItemWithViewController_(self.sidebarVC)

        sidebar_item.setMinimumThickness_(150.0)
        self.addSplitViewItem_(sidebar_item)

        detail_item = NSSplitViewItem.splitViewItemWithViewController_(self.detailVC)
        self.addSplitViewItem_(detail_item)
        return self

    def viewDidAppear(self):
        objc.super(MainSplitVC, self).viewDidAppear()
        try:
            self.splitView().setPosition_ofDividerAtIndex_(200.0, 0)
        except Exception:
            pass


# --------------------------
# Window + Toolbar
# --------------------------

class WindowController(NSWindowController):
    LoadingItemID = "LoadingItem"

    def initWithContentVC_mediaManager_(self, content_vc, mediaManager):
        self = objc.super(WindowController, self).initWithWindow_(
            NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                ((0, 0), (1000, 640)),
                15,  # titled | closable | miniaturizable | resizable
                2,   # buffered
                False
            )
        )
        if self is None:
            return None

        self.mediaManager = mediaManager
        self.window().setTitle_("NavigationSplitView (PyObjC)")
        self.setContentViewController_(content_vc)

        tb = NSToolbar.alloc().initWithIdentifier_("MainTB")
        tb.setDelegate_(self)
        tb.setDisplayMode_(NSToolbarDisplayModeIconOnly)
        self.window().setToolbar_(tb)

        # KVO observe isLoading
        self.mediaManager.addObserver_forKeyPath_options_context_(self, "isLoading", 1, 0)
        return self

    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, obj, change, context):
        if keyPath == "isLoading":
            win = self.window()
            tb = win.toolbar()
            win.setToolbar_(None)
            win.setToolbar_(tb)

    def toolbarAllowedItemIdentifiers_(self, toolbar):
        return [NSToolbarFlexibleSpaceItemIdentifier, self.LoadingItemID, NSToolbarToggleSidebarItemIdentifier]

    def toolbarDefaultItemIdentifiers_(self, toolbar):
        return [NSToolbarFlexibleSpaceItemIdentifier, self.LoadingItemID, NSToolbarToggleSidebarItemIdentifier] if self.mediaManager.isLoading() else [NSToolbarFlexibleSpaceItemIdentifier, NSToolbarToggleSidebarItemIdentifier]

    def toolbar_itemForItemIdentifier_willBeInsertedIntoToolbar_(self, toolbar, itemIdentifier, willBeInserted):
        if itemIdentifier == self.LoadingItemID:
            spinner = NSProgressIndicator.alloc().initWithFrame_(((0, 0), (16, 16)))
            try:
                from AppKit import NSProgressIndicatorStyleSpinning
                spinner.setStyle_(NSProgressIndicatorStyleSpinning)
            except Exception:
                spinner.setStyle_(1)  # spinning
            spinner.setControlSize_(NSControlSizeSmall)
            spinner.setIndeterminate_(True)
            spinner.startAnimation_(None)

            item = NSToolbarItem.alloc().initWithItemIdentifier_(self.LoadingItemID)
            item.setView_(spinner)
            return item
        return None


# --------------------------
# Menu
# --------------------------

def build_main_menu():
    mainMenu = NSMenu.alloc().init()

    appItem = NSMenuItem.alloc().init()
    mainMenu.addItem_(appItem)

    appMenu = NSMenu.alloc().init()
    appName = NSProcessInfo.processInfo().processName()

    appMenu.addItemWithTitle_action_keyEquivalent_(f"About {appName}", "orderFrontStandardAboutPanel:", "")
    appMenu.addItem_(NSMenuItem.separatorItem())
    appMenu.addItemWithTitle_action_keyEquivalent_(f"Hide {appName}", "hide:", "h")
    hideOthers = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Hide Others", "hideOtherApplications:", "h")
    hideOthers.setKeyEquivalentModifierMask_(0x18)  # cmd+option
    appMenu.addItem_(hideOthers)
    appMenu.addItemWithTitle_action_keyEquivalent_("Show All", "unhideAllApplications:", "")
    appMenu.addItem_(NSMenuItem.separatorItem())
    appMenu.addItemWithTitle_action_keyEquivalent_(f"Quit {appName}", "terminate:", "q")
    appItem.setSubmenu_(appMenu)

    fileItem = NSMenuItem.alloc().init()
    mainMenu.addItem_(fileItem)
    fileMenu = NSMenu.alloc().initWithTitle_("File")
    fileMenu.addItemWithTitle_action_keyEquivalent_("Close Window", "performClose:", "w")
    fileItem.setSubmenu_(fileMenu)

    NSApp.setMainMenu_(mainMenu)


# --------------------------
# App Entry
# --------------------------

def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
    build_main_menu()

    now = datetime.now()
    history = [HistoryItem(uuid.uuid4(), now - timedelta(minutes=30 * i)) for i in range(20)]
    mediaManager = MediaManager.alloc().init()

    splitVC = MainSplitVC.alloc().initWithHistory_(history)
    winController = WindowController.alloc().initWithContentVC_mediaManager_(splitVC, mediaManager)
    winController.window().center()
    winController.showWindow_(None)

    # Demo spinner
    mediaManager.setIsLoading_(True)

    class _TimerTarget(NSObject):
        def initWithCallback_(self, cb):
            self = objc.super(_TimerTarget, self).init()
            if self is None:
                return None
            self.cb = cb
            return self
        def fire_(self, _):
            self.cb()

    globals()["_timer_keepalive"] = []
    off = _TimerTarget.alloc().initWithCallback_(lambda: mediaManager.setIsLoading_(False))
    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(3.0, off, "fire:", None, False)
    globals()["_timer_keepalive"].append(off)

    app.activateIgnoringOtherApps_(True)
    app.run()


if __name__ == "__main__":
    main()

