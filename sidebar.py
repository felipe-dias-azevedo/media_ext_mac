import objc
from Cocoa import (
    NSView, NSViewController, NSScrollView, NSTableView, NSTableCellView, NSTableColumn,
    NSVisualEffectView, NSColor, NSFont, NSTextField,
    NSLayoutConstraint, NSMakeRect, NSMakeSize,
    NSTableViewStyleInset, NSVisualEffectMaterialSidebar,
    NSVisualEffectBlendingModeBehindWindow, NSVisualEffectStateActive,
    NSTableViewAnimationSlideDown, NSTableViewAnimationEffectFade, NSLineBreakByTruncatingMiddle
)
from Foundation import NSMutableIndexSet
from sys import argv
from datetime import datetime
from database import MediaDB, DB_FILENAME
from db_path import db_path
from models import MediaItem, HistoryFormatter


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
            title.setLineBreakMode_(NSLineBreakByTruncatingMiddle)
            # TODO: add tooltip to title label

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
