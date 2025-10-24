from Cocoa import (
    NSObject, NSApplication, NSApp, NSWindow,
    NSView, NSViewController, NSScrollView, NSTextView, NSTextField, NSTableCellView,
    NSButton, NSImage, NSBox, NSStackView, NSProgressIndicator,
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
    NSTableView, NSTableColumn, NSImageSymbolConfiguration, NSBeep
)
import Quartz
from UserNotifications import (
    UNUserNotificationCenter,
    UNAuthorizationOptionAlert,
    UNAuthorizationOptionSound,
    UNAuthorizationOptionBadge,
    UNNotificationPresentationOptionAlert,
    UNNotificationPresentationOptionSound,
)
from Foundation import NSMutableIndexSet, NSNotificationCenter, NSBundle
import objc
import os
import threading
from sys import argv
from datetime import datetime
from database import MediaDB, DB_FILENAME
from downloader import Downloader
from user_defaults import UserDefaults
from models import MediaItem, HistoryFormatter
from db_path import db_path
from notifications import send_notification
from menu import buildMenus
from settings import SettingsWindowController


class DownloaderLogger:
    def __init__(self, handler):
        self.content = ""
        self.handler = handler

    def output(self, text):
        self.content += text + "\n"

        if "--dev" in argv:
            print(text)

        self.handler(self.content)

    def debug(self, msg):
        self.output(f"{msg}")

    def info(self, msg):
        self.output(f"[INFO] {msg}")

    def warning(self, msg):
        self.output(f"[WARNING] {msg}")

    def error(self, msg):
        self.output(f"[ERROR] {msg}")

    def reset(self):
        self.content = ""


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
        self.visualEffect = NSVisualEffectView.alloc().init()

        self.db = MediaDB(db_path=db_path(DB_FILENAME, dev_env="--dev" in argv))
        self.data = []

        # center = NSNotificationCenter.defaultCenter()
        # center.addObserver_selector_name_object_(
        #     self, 
        #     objc.selector(self._appWillTerminate_, signature=b"v@:@"),
        #     NSApplication.willTerminateNotification, 
        #     None
        # )

        return self

    def loadView(self):
        view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 250, 350))
        view.setWantsLayer_(True)
        self.setView_(view)
        
        # Add visual effect view first
        self.visualEffect.setMaterial_(NSVisualEffectMaterialSidebar)
        self.visualEffect.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        self.visualEffect.setState_(NSVisualEffectStateActive)
        self.visualEffect.setWantsLayer_(True)
        self.visualEffect.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.view().addSubview_(self.visualEffect)
        
        # Make scroll view transparent
        self.scroll.setDrawsBackground_(False)
        self.table.setBackgroundColor_(NSColor.clearColor())
        
        # Configure table
        self.table.setHeaderView_(None)
        self.table.setRowHeight_(48.0)
        self.table.setIntercellSpacing_(NSMakeSize(0.0, 0.0))
        self.table.setStyle_(NSTableViewStyleInset)

        # Add column
        col = NSTableColumn.alloc().initWithIdentifier_("main")
        self.table.addTableColumn_(col)
        self.table.setDelegate_(self)
        self.table.setDataSource_(self)
        
        # Configure scroll view
        self.scroll.setDocumentView_(self.table)
        self.scroll.setHasVerticalScroller_(True)
        self.scroll.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.view().addSubview_(self.scroll)

        # Update constraints to include visual effect view
        NSLayoutConstraint.activateConstraints_([
            # Pin visual effect to all edges
            self.visualEffect.topAnchor().constraintEqualToAnchor_(self.view().topAnchor()),
            self.visualEffect.leadingAnchor().constraintEqualToAnchor_(self.view().leadingAnchor()),
            self.visualEffect.trailingAnchor().constraintEqualToAnchor_(self.view().trailingAnchor()),
            self.visualEffect.bottomAnchor().constraintEqualToAnchor_(self.view().bottomAnchor()),
            
            # Existing scroll view constraints
            self.scroll.leadingAnchor().constraintEqualToAnchor_(self.view().leadingAnchor()),
            self.scroll.trailingAnchor().constraintEqualToAnchor_(self.view().trailingAnchor()),
            self.scroll.topAnchor().constraintEqualToAnchor_(self.view().topAnchor()),
            self.scroll.bottomAnchor().constraintEqualToAnchor_(self.view().bottomAnchor()),
        ])

    def viewDidLoad(self):
        objc.super(SidebarVC, self).viewDidLoad()
        self.getHistoryData_(None)

    # Data source
    def numberOfRowsInTableView_(self, tableView):
        return len(self.data)

    # Group rows
    def tableView_isGroupRow_(self, tableView, row):
        return bool(self.data[row].isGroup)

    def tableView_shouldSelectRow_(self, tableView, row):
        return self.data[row].isGroup == False

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
        
    def addRow_(self, obj):
        if obj is None:
            return
        
        idxs = NSMutableIndexSet.indexSet()

        if len(self.data) > 0:
            firstIndex = self.data[0]
            addGroup = not (firstIndex.isGroup and firstIndex.title == "Just now")
        else:
            addGroup = True

        items = [MediaItem.item(obj["file"], datetime.now().strftime("%y/%m/%d, %H:%M:%S"))]
        if (addGroup):
            items.insert(0, MediaItem.group("Just now"))

            self.data[0:0] = items[:2]

            idxs.addIndex_(0)
            idxs.addIndex_(1)
        else:
            self.data[1:1] = items

            idxs.addIndex_(1)

        self.table.beginUpdates()
        self.table.insertRowsAtIndexes_withAnimation_(
            idxs, (NSTableViewAnimationSlideDown | NSTableViewAnimationEffectFade)
        )
        self.table.endUpdates()

        self.table.scrollRowToVisible_(0)

        self.performSelectorOnMainThread_withObject_waitUntilDone_("addHistoryData:", obj, False)

    def getHistoryData_(self, sender=None):
        self.data = HistoryFormatter().format(self.db.select_history())
        self.table.reloadData()

    def addHistoryData_(self, obj):
        self.db.insert_history(obj["file"], obj["url"])

    def _appWillTerminate_(self, note):
        self.db.close()


# -----------------------------
# Status Pill
# -----------------------------

class StatusPill(NSView):
    KindNone = 0
    KindSuccess = 1
    KindProgress = 2
    KindError = 3

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
        self.box.setBorderWidth_(1)
        self.box.setBorderColor_(NSColor.separatorColor())
        self.box.setFillColor_(NSColor.controlBackgroundColor())
        self.addSubview_(self.box)

        conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_(14.0, NSFontWeightSemibold)
        self.icon.setSymbolConfiguration_(conf)
        img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("checkmark", None)
        self.icon.setContentTintColor_(NSColor.systemGreenColor())
        self.icon.setImage_(img)

        self.spinner.setStyle_(NSProgressIndicatorStyleSpinning)  # NSProgressIndicatorStyleSpinning
        self.spinner.setControlSize_(1)  # small
        self.spinner.setDisplayedWhenStopped_(False)
        self.label.setFont_(NSFont.systemFontOfSize_weight_(14.0, NSFontWeightMedium))

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
        self.reset_()
        return self

    def setKind_message_(self, kind, msg):
        if kind == self.KindNone:
            self.reset_()    
        elif kind == self.KindSuccess:
            self.spinner.stopAnimation_(None)
            self.spinner.setHidden_(True)
            self.icon.setHidden_(False)
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("checkmark", None)
            self.icon.setImage_(img)
            self.icon.setContentTintColor_(NSColor.systemGreenColor())
            self.label.setStringValue_(msg)
            self.label.setTextColor_(NSColor.systemGreenColor())
        elif kind == self.KindError:
            self.spinner.stopAnimation_(None)
            self.spinner.setHidden_(True)
            self.icon.setHidden_(False)
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("xmark", None)
            self.icon.setImage_(img)
            self.icon.setContentTintColor_(NSColor.systemRedColor())
            self.label.setStringValue_(msg)
            self.label.setTextColor_(NSColor.systemRedColor())
        else:
            self.icon.setHidden_(True)
            self.spinner.setHidden_(False)
            self.spinner.startAnimation_(None)
            self.label.setStringValue_(msg)
            self.label.setTextColor_(NSColor.labelColor())

    def reset_(self, sender=None):
        self.icon.setHidden_(True)
        self.spinner.setHidden_(True)
        self.label.setStringValue_("")
        self.label.setTextColor_(NSColor.labelColor())


# -----------------------------
# Content VC (right side)
# -----------------------------

class ContentVC(NSViewController):
    def init(self):
        self = objc.super(ContentVC, self).init()
        if self is None:
            return None
        self.sidebarVC = None  # to be set by parent

        self.urlContainer = NSView.alloc().init()
        self.urlInlineLabel = NSTextField.labelWithString_("URL")
        self.urlField = NSTextField.alloc().init()
        self.pasteButton = NSButton.alloc().init()
        self.extractButton = NSButton.alloc().init()
        self.statusPill = StatusPill.alloc().init()

        self.logger = DownloaderLogger(self._enqueue_log)
        self.userDefaults = UserDefaults()
        self.downloader = Downloader(self.logger)

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
            self.urlContainer.layer().setCornerRadius_(6.0)
            self.urlContainer.layer().setBorderWidth_(1)
            self.urlContainer.layer().setBorderColor_(NSColor.separatorColor().CGColor())
            self.urlContainer.layer().setBackgroundColor_(NSColor.quaternarySystemFillColor().CGColor())

        self.urlInlineLabel.setFont_(NSFont.systemFontOfSize_(12.0))
        self.urlInlineLabel.setTextColor_(NSColor.labelColor())

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
        self.extractButton.setBordered_(False)
        self.extractButton.setContentTintColor_(NSColor.whiteColor())
        self.extractButton.setWantsLayer_(True)
        self.extractButton.setFont_(NSFont.systemFontOfSize_weight_(NSFont.systemFontSize(), NSFontWeightSemibold))
        layer = self.extractButton.layer()
        layer.setBackgroundColor_(NSColor.systemBlueColor().CGColor())
        layer.setCornerRadius_(8.0)
        layer.setMasksToBounds_(True)


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
        self.logText.setString_("")

        self.logScroll.setHasVerticalScroller_(True)
        self.logScroll.setBorderType_(NSNoBorder)
        self.logScroll.setDrawsBackground_(False)

        # Logs container with rounded border
        self.logContainer = NSView.alloc().init()
        self.logContainer.setWantsLayer_(True)
        if self.logContainer.layer() is None:
            self.view().setWantsLayer_(True)
            self.logContainer.setWantsLayer_(True)
        if self.logContainer.layer() is not None:
            self.logContainer.layer().setCornerRadius_(8.0)
            self.logContainer.layer().setBorderWidth_(1)
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
            self.urlContainer.topAnchor().constraintEqualToAnchor_constant_(self.view().topAnchor(), 68.0),
            self.urlContainer.trailingAnchor().constraintEqualToAnchor_constant_(self.extractButton.leadingAnchor(), -12.0),
            self.urlContainer.heightAnchor().constraintEqualToConstant_(32.0),

            self.urlInlineLabel.leadingAnchor().constraintEqualToAnchor_constant_(self.urlContainer.leadingAnchor(), 10.0),
            self.urlInlineLabel.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),

            self.urlField.leadingAnchor().constraintEqualToAnchor_constant_(self.urlInlineLabel.trailingAnchor(), 10.0),
            self.urlField.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),
            self.urlField.trailingAnchor().constraintEqualToAnchor_constant_(self.pasteButton.leadingAnchor(), -8.0),

            self.pasteButton.trailingAnchor().constraintEqualToAnchor_constant_(self.urlContainer.trailingAnchor(), -10.0),
            self.pasteButton.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),

            self.extractButton.trailingAnchor().constraintEqualToAnchor_constant_(self.view().trailingAnchor(), -24.0),
            self.extractButton.centerYAnchor().constraintEqualToAnchor_(self.urlContainer.centerYAnchor()),
            self.extractButton.heightAnchor().constraintEqualToConstant_(32.0),
            self.extractButton.widthAnchor().constraintEqualToConstant_(76.0),

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
        if not s:
            NSBeep()
            return
        self.urlField.setStringValue_(s)

    def _enqueue_log(self, text):
        self.performSelectorOnMainThread_withObject_waitUntilDone_("appendLog:", text, False)

    def appendLog_(self, text):
        self.logText.setString_(text)
        self.logText.scrollRangeToVisible_(NSMakeRange(len(text), 0))

    def extract_(self, sender):
        text = self.urlField.stringValue().strip()
        if not text:
            NSBeep()
            return

        if not text.lower().startswith("https://"): # TODO: add proper validation
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Invalid URL")
            alert.setInformativeText_("Please enter a valid URL.")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return

        self.statusPill.setKind_message_(StatusPill.KindProgress, "Downloading")
        self.logger.reset()
        self.logger.info("Extract started.")
        self.setBusy_(True)
        threading.Thread(target=self._download_thread, args=(text,), daemon=True).start()

    def _download_thread(self, url):
        try:
            normalization = self.userDefaults.getNormalization()
            self.logger.info(f"Using normalization: {normalization}")

            path = self.downloader.download(url, normalization=normalization)
            self.logger.info(f"Download finished successfully: {path}")
            
            self.performSelectorOnMainThread_withObject_waitUntilDone_("finishExtract:", path, True)

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            self.statusPill.setKind_message_(StatusPill.KindError, "Failed")
        finally:
            self.performSelectorOnMainThread_withObject_waitUntilDone_("setBusy:", False, False)

    def finishExtract_(self, src_path):
        try:
            self.statusPill.setKind_message_(StatusPill.KindProgress, "Saving File")
            file = self.presentSavePanelForPath_(src_path)
            self.addToSidebar_({
                "file": os.path.basename(file),
                "url": self.urlField.stringValue().strip()
            })
            send_notification("Extraction Completed", f"File saved: {os.path.basename(file)}")
            self.statusPill.setKind_message_(StatusPill.KindSuccess, "Success")
        except Exception as e:
            self.logger.error(f"Save failed: {e}")
            self.statusPill.setKind_message_(StatusPill.KindError, "Failed")
        finally:
            self.setBusy_(False)

    def setBusy_(self, is_busy):
        self.extractButton.setEnabled_(not is_busy)
        self.urlField.setEnabled_(not is_busy)
        self.urlField.setEditable_(not is_busy)

        if not is_busy:
            self.urlField.setStringValue_("")

    def presentSavePanelForPath_(self, src_path):

        save_path = self.openSavePanel_(src_path)
        while save_path is None:
            save_path = self.openSavePanel_(src_path)

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
        
    def addToSidebar_(self, newMediaItem):
        self.sidebarVC.performSelectorOnMainThread_withObject_waitUntilDone_(
            "addRow:", newMediaItem, True
        )

# -----------------------------
# Split container
# -----------------------------

class RootSplitVC(NSSplitViewController):
    def viewDidLoad(self):
        objc.super(RootSplitVC, self).viewDidLoad()
        leftVC = SidebarVC.alloc().init()
        rightVC = ContentVC.alloc().init()
        rightVC.sidebarVC = leftVC
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
    bundle = NSBundle.mainBundle()
    if bundle and bundle.resourcePath():
        bundled_ffmpeg = os.path.join(bundle.resourcePath(), "ffmpeg")
        if os.path.exists(bundled_ffmpeg):
            os.environ["IMAGEIO_FFMPEG_EXE"] = bundled_ffmpeg

    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
