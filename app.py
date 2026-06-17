from Cocoa import (
    NSObject, NSApplication, NSApp, NSWindow,
    NSView, NSViewController, NSScrollView, NSTextView, NSTextField, NSTableCellView,
    NSButton, NSBox, NSStackView, NSProgressIndicator,
    NSSplitViewController, NSSplitViewItem, NSToolbar, NSImageView,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSTableViewStyleInset,
    NSWindowStyleMaskMiniaturizable, NSWindowStyleMaskResizable, NSBackingStoreBuffered,
    NSApplicationActivationPolicyRegular, NSFont, NSColor, NSPasteboard,
    NSStringPboardType, NSLayoutConstraint, NSLayoutConstraintOrientationHorizontal,
    NSMutableAttributedString, NSMakeSize, NSMakeRect, NSMakeRange,
    NSUserInterfaceLayoutOrientationHorizontal, NSBoxCustom, NSMomentaryPushInButton, NSControlSizeLarge,
    NSBezelStyleShadowlessSquare, NSImageOnly, NSFocusRingTypeNone, NSBezelStyleRounded, NSProgressIndicatorStyleSpinning,
    NSTextLayoutOrientationHorizontal, NSLineBreakByTruncatingMiddle, NSFontWeightMedium,
    NSSavePanel, NSModalResponseOK, NSAlert, NSFontWeightSemibold, NSNoBorder,
    NSVisualEffectView, NSVisualEffectMaterialSidebar, NSToolbarSidebarTrackingSeparatorItemIdentifier,
    NSVisualEffectBlendingModeBehindWindow, NSVisualEffectStateActive, NSWindowTitleHidden,
    NSToolbarDisplayModeIconOnly, NSToolbarToggleSidebarItemIdentifier, NSToolbarFlexibleSpaceItemIdentifier,
    NSToolbarItem, NSWindowTabbingModeDisallowed, NSWindowStyleMaskFullSizeContentView, NSWindowToolbarStyleUnified,
    NSTableViewAnimationSlideUp, NSTableViewAnimationSlideDown, NSTableViewAnimationEffectFade,
    NSUserDefaults
)
from AppKit import (
    NSTableView, NSTableColumn, NSBeep
)
from UserNotifications import (
    UNUserNotificationCenter,
    UNAuthorizationOptionAlert,
    UNAuthorizationOptionSound,
    UNAuthorizationOptionBadge,
    UNNotificationPresentationOptionAlert,
    UNNotificationPresentationOptionSound,
)
from Foundation import (
    NSMutableIndexSet, NSNotificationCenter, NSBundle
)
import objc
import os
import threading
from sys import argv
from datetime import datetime
from database import MediaDB, DB_FILENAME
from downloader import Downloader
from progress import ProgressStepsView
from user_defaults import UserDefaults
from models import MediaItem, HistoryFormatter
from db_path import db_path
from notifications import send_notification
from menu import buildMenus
from settings import SettingsWindowController
from url_row import URLRowView
from sidebar import SidebarVC
from log_window_controller import LogWindowController
from enum import Enum

class Progresser:
    def __init__(self, handler):
        self.handler = handler
        self.downloading = False
        self.postprocessing = False

    def download(self, msg):
        self.downloading = True
        self.handler((ProgressStatus.UPDATE, "Downloading", msg, None))
    
    def finish_download(self, msg):
        self.downloading = False
        self.handler((ProgressStatus.SUCCESS, "Download Completed", msg, None))

    def postprocess(self, msg):
        self.postprocessing = True
        self.handler((ProgressStatus.BEGIN, "Post Processing", msg, None))

    def finish_postprocess(self, msg):
        self.postprocessing = False
        self.handler((ProgressStatus.SUCCESS, "Post Processing Completed", msg, None))

class ProgressStatus(Enum):
    ADD = 0
    BEGIN = 1
    UPDATE = 2
    SUCCESS = 3
    ERROR = 4


# -----------------------------
# Content VC (right side)
# -----------------------------

class ContentVC(NSViewController):

    def init(self):
        self = objc.super(ContentVC, self).init()
        if self is None:
            return None
        self.sidebarVC = None  # to be set by parent

        # UI elements
        self.urlRow = None
        self.progressSteps = ProgressStepsView.alloc().init()
        self.progressSteps.setHidden_(True)
        self.logger = None
        self.downloader = None
        self.progresser = Progresser(self._enqueue_progress)
        self.userDefaults = UserDefaults()

        return self

    def viewDidAppear(self):
        objc.super(ContentVC, self).viewDidAppear()
        self.urlRow.extractButton.setKeyEquivalent_("\r")
        if self.view().window() is not None:
            self.view().window().setDefaultButtonCell_(self.urlRow.extractButton.cell())

    def loadView(self):
        root = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 400))
        self.setView_(root)

        # URL row component (input, paste, extract button)
        self.urlRow = URLRowView.alloc().initWithTarget_action_(self, "extract:")
        self.urlRow.setTranslatesAutoresizingMaskIntoConstraints_(False)

        # ---- Add outer subviews
        for sub in (self.urlRow, self.progressSteps):
            sub.setTranslatesAutoresizingMaskIntoConstraints_(False)
            root.addSubview_(sub)

        # ---- Constraints (outer)
        NSLayoutConstraint.activateConstraints_([
            self.urlRow.leadingAnchor().constraintEqualToAnchor_constant_(root.leadingAnchor(), 24.0),
            self.urlRow.topAnchor().constraintEqualToAnchor_constant_(root.topAnchor(), 68.0),
            self.urlRow.trailingAnchor().constraintEqualToAnchor_constant_(root.trailingAnchor(), -24.0),
            self.urlRow.heightAnchor().constraintEqualToConstant_(32.0),

            self.progressSteps.leadingAnchor().constraintEqualToAnchor_(self.urlRow.leadingAnchor()),
            self.progressSteps.trailingAnchor().constraintEqualToAnchor_(self.urlRow.trailingAnchor()),
            self.progressSteps.topAnchor().constraintEqualToAnchor_constant_(self.urlRow.bottomAnchor(), 12.0),
            self.progressSteps.heightAnchor().constraintGreaterThanOrEqualToConstant_(32.0),
        ])

    def viewDidLayout(self):
        objc.super(ContentVC, self).viewDidLayout()

    def setLogger_(self, logger):
        self.logger = logger
        self.downloader = Downloader(self.logger, self.progresser)

    def _enqueue_log(self, text):
        self.performSelectorOnMainThread_withObject_waitUntilDone_("appendLog:", text, False)

    def extract_(self, sender):
        text = self.urlRow.urlValue().strip()
        if not text:
            NSBeep()
            return

        # TODO: check if is youtube url and contains list query 
        if not text.lower().startswith("https://"):  # TODO: add proper validation
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Invalid URL")
            alert.setInformativeText_("Please enter a valid URL.")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return

        if self.progressSteps.isHidden():
            self.progressSteps.setHidden_(False)
        self.progressSteps.reset()
        self.logger.reset()
        self.logger.info("Extract started.")
        self.setBusy_(True)
        threading.Thread(target=self._download_thread, args=(text,), daemon=True).start()

    def _enqueue_progress(self, args):
        self.performSelectorOnMainThread_withObject_waitUntilDone_("updateProgress:", args, False)

    def updateProgress_(self, args):
        status, title, description, icon = args
        match status:
            case ProgressStatus.ADD:
                self.progressSteps.addStep_description_icon_(title, description, icon)
            case ProgressStatus.BEGIN:
                self.progressSteps.beginCurrentStep_description_icon_(title, description, None)
            case ProgressStatus.UPDATE:
                self.progressSteps.updateCurrentStep_description_(title, description)
            case ProgressStatus.SUCCESS:
                self.progressSteps.finishCurrentStepSuccess_description_(title, description)
            case ProgressStatus.ERROR:
                self.progressSteps.finishCurrentStepError_description_(title, description)

    def _download_thread(self, url):
        try:
            normalization = self.userDefaults.getNormalization()
            normalization_text = f"Using normalization: {normalization}"
            self.logger.info(normalization_text)
            self.performSelectorOnMainThread_withObject_waitUntilDone_("updateProgress:", (ProgressStatus.ADD, "Normalization", normalization_text, "gearshape"), False)

            self.performSelectorOnMainThread_withObject_waitUntilDone_("updateProgress:", (ProgressStatus.BEGIN, "Downloading", "Starting Download...", None), False)
            path = self.downloader.download(url, normalization=normalization)
            self.logger.info(f"Download finished successfully: {path}")
            send_notification("Download Completed", os.path.basename(path))

            self.performSelectorOnMainThread_withObject_waitUntilDone_("finishExtract:", path, True)

        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.performSelectorOnMainThread_withObject_waitUntilDone_("updateProgress:", (ProgressStatus.ERROR, "Error", e, None), False)
        finally:
            self.performSelectorOnMainThread_withObject_waitUntilDone_("setBusy:", False, False)

    def finishExtract_(self, src_path):
        try:
            self.progressSteps.beginCurrentStep_description_icon_("Saving File", "Choose where to save...")
            file = self.presentSavePanelForPath_(src_path)
            
            if file is None:
                self.logger.warning("Save cancelled by user.")
                self.progressSteps.finishCurrentStepError_description_("Save Failed", "Cancelled by user.")
                return

            media_item = MediaItem.item(
                path=file,
                title=os.path.basename(file), 
                url=self.urlRow.urlValue().strip(), 
                timestamp=datetime.now().timestamp(),
            )
            self.progressSteps.finishCurrentStepSuccess_description_("Save File Completed", "File: " + os.path.basename(file))
            self.sidebarVC.addRowToSidebar_(media_item)
        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            self.progressSteps.finishCurrentStepError_description_("Save Failed", e)
        finally:
            self.setBusy_(False)

    def setBusy_(self, is_busy):
        self.urlRow.setEnabled_(not is_busy)
        if not is_busy:
            self.urlRow.clearURL()

    def presentSavePanelForPath_(self, src_path):
        save_path = self.openSavePanel_(src_path)
        if save_path is None:
            return None

        self.logger.info(f"Saving to: {save_path}")
        self.downloader.move_file(src_path, save_path)
        self.logger.info("File saved successfully.")
        return save_path

    def openSavePanel_(self, src_path):
        try:
            panel = NSSavePanel.savePanel()
            panel.setAllowsOtherFileTypes_(False)
            panel.setAllowedFileTypes_(["mp3"])
            suggested = os.path.basename(src_path)
            panel.setNameFieldStringValue_(suggested)
            resp = panel.runModal()
            if not resp or resp != NSModalResponseOK:
                return None
            return panel.URL().path()
        except Exception as e:
            self.logger.error(f"Error showing save dialog: {e}")
            return None


# -----------------------------
# Split container
# -----------------------------

class RootSplitVC(NSSplitViewController):
    def viewDidLoad(self):
        objc.super(RootSplitVC, self).viewDidLoad()
        leftVC = SidebarVC.alloc().init()
        rightVC = ContentVC.alloc().init()
        rightVC.sidebarVC = leftVC
        self.contentVC = rightVC
        rightVC.setLogger_(LogWindowController.sharedController().logger)
        left = NSSplitViewItem.sidebarWithViewController_(leftVC)
        right = NSSplitViewItem.splitViewItemWithViewController_(rightVC)
        self.addSplitViewItem_(left)
        self.addSplitViewItem_(right)


class NotificationDelegate(NSObject):
    # Show banners/sound even when your app is frontmost
    def userNotificationCenter_willPresentNotification_withCompletionHandler_(self, center, notification, completionHandler):
        completionHandler(UNNotificationPresentationOptionAlert | UNNotificationPresentationOptionSound)

# -----------------------------
# App Delegate
# -----------------------------

class AppDelegate(NSObject):
    window = objc.ivar()
    splitVC = objc.ivar()

    def applicationDidFinishLaunching_(self, notification):
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        buildMenus()

        self.notificationDelegate = NotificationDelegate.alloc().init()
        center = UNUserNotificationCenter.currentNotificationCenter()
        center.setDelegate_(self.notificationDelegate)
        opts = UNAuthorizationOptionAlert | UNAuthorizationOptionSound | UNAuthorizationOptionBadge
        def _auth_done(granted, error):
            print("Notifications granted:", bool(granted), "error:", error)
        center.requestAuthorizationWithOptions_completionHandler_(opts, _auth_done)

        self.splitVC = RootSplitVC.alloc().init()

        rect = NSMakeRect(0, 0, 840, 620)
        style = (NSWindowStyleMaskTitled |
                 NSWindowStyleMaskClosable |
                 NSWindowStyleMaskMiniaturizable |
                 NSWindowStyleMaskResizable)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Media.Ext")
        self.window.setStyleMask_(self.window.styleMask() | NSWindowStyleMaskFullSizeContentView)
        self.window.setToolbarStyle_(NSWindowToolbarStyleUnified)
        self.window.setContentViewController_(self.splitVC)
        self.window.setContentSize_(NSMakeSize(840, 620))
        self.window.center()
        self.window.makeKeyAndOrderFront_(None)
        self.window.setTabbingMode_(NSWindowTabbingModeDisallowed)
        self.window.setContentMinSize_(NSMakeSize(600, 360))

        toolbar = NSToolbar.alloc().initWithIdentifier_("MediaExtToolbar")
        toolbar.setDelegate_(self)
        toolbar.setAutosavesConfiguration_(False)
        toolbar.setAllowsUserCustomization_(False)
        toolbar.setDisplayMode_(NSToolbarDisplayModeIconOnly)
        self.window.setToolbar_(toolbar)

        NSApp.activateIgnoringOtherApps_(True)

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        return True
    
    def showPreferences_(self, sender):
        SettingsWindowController.sharedController().showWindow_(sender)

    def showLogs_(self, sender):
        LogWindowController.sharedController().showWindow_(sender)
    
    def toolbarAllowedItemIdentifiers_(self, toolbar):
        return [NSToolbarToggleSidebarItemIdentifier, NSToolbarSidebarTrackingSeparatorItemIdentifier, NSToolbarFlexibleSpaceItemIdentifier]

    def toolbarDefaultItemIdentifiers_(self, toolbar):
        return [NSToolbarToggleSidebarItemIdentifier, NSToolbarSidebarTrackingSeparatorItemIdentifier, NSToolbarFlexibleSpaceItemIdentifier]
    
    def toolbar_itemForItemIdentifier_willBeInsertedIntoToolbar_(self, toolbar, identifier, flag):
        if identifier == NSToolbarToggleSidebarItemIdentifier:
            item = NSToolbarItem.alloc().initWithItemIdentifier_(identifier)
            item.setLabel_("Sidebar")
            item.setPaletteLabel_("Toggle Sidebar")
            item.setTarget_(self.splitVC)
            item.setAction_("toggleSidebar:")
            return item


def main():
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
