import objc
from Cocoa import (
    NSMenu, NSMenuItem,
    NSView, NSViewController, NSScrollView, NSTableView, NSTableCellView, NSTableColumn,
    NSVisualEffectView, NSColor, NSFont, NSTextField,
    NSPasteboard, NSStringPboardType,
    NSLayoutConstraint, NSMakeRect, NSMakeSize,
    NSTableViewStyleSourceList, NSVisualEffectMaterialSidebar,
    NSVisualEffectBlendingModeBehindWindow, NSVisualEffectStateActive,
    NSTableViewAnimationSlideDown, NSTableViewAnimationEffectFade, NSLineBreakByTruncatingTail,
    NSFontWeightMedium, NSFontWeightBold,
)
from Foundation import NSMutableIndexSet
from sys import argv
from datetime import datetime
from database import MediaDB, DB_FILENAME
from db_path import db_path
from models import MediaItem, HistoryFormatter


class SidebarTableView(NSTableView):
    def menuForEvent_(self, event):
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        row = self.rowAtPoint_(point)
        if row == -1:
            return None

        delegate = self.delegate()
        if delegate and hasattr(delegate, 'tableView_menuForEvent_'):
            return delegate.tableView_menuForEvent_(self, event)
        return None


# TODO: Add search/filter functionality, e.g. a search field at the top of the sidebar that filters the history items in real time as the user types. This would be especially useful as the history grows over time.

class SidebarVC(NSViewController, protocols=[objc.protocolNamed("NSTableViewDataSource"),
                                             objc.protocolNamed("NSTableViewDelegate")]):
    def init(self):
        self = objc.super(SidebarVC, self).init()
        if self is None:
            return None
        self.table = SidebarTableView.alloc().init()
        self.scroll = NSScrollView.alloc().init()
        self.visualEffect = NSVisualEffectView.alloc().init()

        self.db = MediaDB(db_path=db_path(DB_FILENAME, dev_env="--dev" in argv))
        self.data = []
        self._contextMenuRow = None
        self._contextMenuActionPerformed = False

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
        self.table.setRowHeight_(44.0)
        self.table.setIntercellSpacing_(NSMakeSize(0.0, 0.0))
        self.table.setStyle_(NSTableViewStyleSourceList)

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
        # return self.data[row].isGroup == False
        return False

    # Views per row
    def tableView_viewForTableColumn_row_(self, tableView, tableColumn, row):
        item = self.data[row]
        v = NSTableCellView.alloc().init()

        if item.isGroup:
            effectView = NSVisualEffectView.alloc().init()
            effectView.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
            effectView.setMaterial_(NSVisualEffectMaterialSidebar)
            effectView.setState_(NSVisualEffectStateActive)
            effectView.setWantsLayer_(True)
            effectView.setTranslatesAutoresizingMaskIntoConstraints_(False)

            label = NSTextField.labelWithString_(item.title)
            label.setFont_(NSFont.systemFontOfSize_weight_(NSFont.systemFontSize(), NSFontWeightBold))
            label.setTextColor_(NSColor.tertiaryLabelColor())
            label.setDrawsBackground_(False)
            label.setBezeled_(False)
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)

            effectView.addSubview_(label)
            v.addSubview_(effectView)
            
            NSLayoutConstraint.activateConstraints_([
                effectView.leadingAnchor().constraintEqualToAnchor_(v.leadingAnchor()),
                effectView.trailingAnchor().constraintEqualToAnchor_(v.trailingAnchor()),
                effectView.topAnchor().constraintEqualToAnchor_(v.topAnchor()),
                effectView.heightAnchor().constraintEqualToConstant_(44),

                label.leadingAnchor().constraintEqualToAnchor_constant_(effectView.leadingAnchor(), 18),
                label.trailingAnchor().constraintLessThanOrEqualToAnchor_constant_(effectView.trailingAnchor(), -10),
                label.centerYAnchor().constraintEqualToAnchor_(v.centerYAnchor()),
            ])
            return v
        else:
            title = NSTextField.labelWithString_(item.title)
            title.setFont_(NSFont.systemFontOfSize_weight_(NSFont.systemFontSize(), NSFontWeightMedium))
            title.setLineBreakMode_(NSLineBreakByTruncatingTail)
            title.setToolTip_(item.title)

            sub = NSTextField.labelWithString_(item.timestamp)
            sub.setFont_(NSFont.systemFontOfSize_(NSFont.smallSystemFontSize()))
            sub.setLineBreakMode_(NSLineBreakByTruncatingTail)
            sub.setTextColor_(NSColor.secondaryLabelColor())

            v.addSubview_(title)
            v.addSubview_(sub)
            title.setTranslatesAutoresizingMaskIntoConstraints_(False)
            sub.setTranslatesAutoresizingMaskIntoConstraints_(False)
            NSLayoutConstraint.activateConstraints_([
                title.leadingAnchor().constraintEqualToAnchor_constant_(v.leadingAnchor(), 2.0),
                title.trailingAnchor().constraintEqualToAnchor_constant_(v.trailingAnchor(), -2.0),
                title.topAnchor().constraintEqualToAnchor_constant_(v.topAnchor(), 6.0),

                sub.leadingAnchor().constraintEqualToAnchor_(title.leadingAnchor()),
                sub.trailingAnchor().constraintEqualToAnchor_(title.trailingAnchor()),
                sub.topAnchor().constraintEqualToAnchor_constant_(title.bottomAnchor(), 0.0),
                sub.bottomAnchor().constraintEqualToAnchor_constant_(v.bottomAnchor(), -6.0),
            ])
            return v

    def tableView_menuForEvent_(self, tableView, event):
        point = tableView.convertPoint_fromView_(event.locationInWindow(), None)
        row = tableView.rowAtPoint_(point)
        if row == -1 or self.data[row].isGroup:
            return None

        idxs = NSMutableIndexSet.indexSet()
        idxs.addIndex_(row)
        tableView.selectRowIndexes_byExtendingSelection_(idxs, False)

        self._contextMenuRow = row
        self._contextMenuActionPerformed = False

        menu = NSMenu.alloc().initWithTitle_("")
        menu.setDelegate_(self)

        copy_title_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Copy File Name", "copyTitle:", "")
        copy_title_item.setTarget_(self)
        copy_title_item.setRepresentedObject_(row)
        menu.addItem_(copy_title_item)

        copy_url_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Copy URL", "copyURL:", "")
        copy_url_item.setTarget_(self)
        copy_url_item.setRepresentedObject_(row)
        menu.addItem_(copy_url_item)

        return menu

    def copyTitle_(self, sender):
        self._contextMenuActionPerformed = True
        row = sender.representedObject()
        if row is None or row == -1:
            return

        title = self.data[row].title
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setString_forType_(title, NSStringPboardType)

    def copyURL_(self, sender):
        self._contextMenuActionPerformed = True
        row = sender.representedObject()
        if row is None or row == -1:
            return

        url = self.data[row].url
        pasteboard = NSPasteboard.generalPasteboard()
        pasteboard.clearContents()
        pasteboard.setString_forType_(url, "public.utf8-plain-text")

    def menuDidClose_(self, menu):
        if not self._contextMenuActionPerformed:
            self.table.deselectAll_(None)
        self._contextMenuRow = None
        self._contextMenuActionPerformed = False

    def addRow_(self, obj):
        if obj is None:
            return
        
        idxs = NSMutableIndexSet.indexSet()

        if len(self.data) > 0:
            firstIndex = self.data[0]
            addGroup = not (firstIndex.isGroup and firstIndex.title == "Just now")
        else:
            addGroup = True

        items = [MediaItem.item(obj["file"], obj["url"], datetime.now().strftime("%y/%m/%d, %H:%M:%S"))]
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
