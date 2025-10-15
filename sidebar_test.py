# notes_sidebar_safe.py
import objc, datetime, random
from dataclasses import dataclass
from Foundation import NSObject
from AppKit import (
    NSApplication, NSWindow, NSWindowStyleMaskTitled, NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable, NSWindowStyleMaskResizable, NSMakeRect,
    NSColor, NSViewController, NSView, NSVisualEffectView,
    NSVisualEffectMaterialSidebar, NSVisualEffectBlendingModeBehindWindow,
    NSScrollView, NSClipView, NSCollectionView, NSCollectionViewItem,
    NSCollectionViewFlowLayout, NSUserInterfaceItemIdentifier,
    NSLayoutConstraint, NSLayoutAttributeLeading, NSLayoutAttributeTrailing,
    NSLayoutAttributeTop, NSLayoutAttributeBottom, NSLayoutRelationEqual,
    NSTextField
)
from PyObjCTools import AppHelper

# ----- Try to grab modern list APIs (macOS 11+) -----
def lookup(name):
    try:
        return objc.lookUpClass(name)
    except objc.error:
        return None

NSCollectionViewListCell = lookup("NSCollectionViewListCell")
NSCollectionLayoutListConfiguration = lookup("NSCollectionLayoutListConfiguration")
NSCollectionViewCompositionalLayout = lookup("NSCollectionViewCompositionalLayout")

# Constant may not be exported by name in older bridges
try:
    from AppKit import NSCollectionViewElementKindSectionHeader
except Exception:
    NSCollectionViewElementKindSectionHeader = "NSCollectionElementKindSectionHeader"

# ---------- Fake data ----------
@dataclass(frozen=True)
class Note:
    title: str
    snippet: str
    date: datetime.datetime

SECTIONS = ("Today", "Yesterday", "Last 7 Days", "Older")

def bucket(dt: datetime.datetime) -> int:
    today = datetime.date.today()
    d = dt.date()
    if d == today: return 0
    if d == today - datetime.timedelta(days=1): return 1
    if d >= today - datetime.timedelta(days=6): return 2
    return 3

def generate_notes(n=24):
    now = datetime.datetime.now()
    out = []
    for i in range(n):
        delta = random.randint(0, 20)
        when = now - datetime.timedelta(days=delta, hours=random.randint(0, 23))
        out.append(Note(f"Note {i+1}", "Short preview of the note…", when))
    return out

CellID   = NSUserInterfaceItemIdentifier("cell")
HeaderID = NSUserInterfaceItemIdentifier("header")

class ViewController(NSViewController):
    def loadView(self):
        self.view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 320, 600))

        # Background blur
        bg = NSVisualEffectView.alloc().initWithFrame_(self.view.frame())
        bg.setMaterial_(NSVisualEffectMaterialSidebar)
        bg.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        bg.setState_(1)  # followsWindowActiveState
        bg.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.view.addSubview_(bg)

        for attr in (NSLayoutAttributeLeading, NSLayoutAttributeTrailing,
                     NSLayoutAttributeTop, NSLayoutAttributeBottom):
            self.view.addConstraint_(
                NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                    bg, attr, NSLayoutRelationEqual, self.view, attr, 1.0, 0.0
                )
            )

        # Scroll view
        scroll = NSScrollView.alloc().initWithFrame_(bg.frame())
        scroll.setDrawsBackground_(False)
        scroll.setTranslatesAutoresizingMaskIntoConstraints_(False)
        bg.addSubview_(scroll)
        for attr in (NSLayoutAttributeLeading, NSLayoutAttributeTrailing,
                     NSLayoutAttributeTop, NSLayoutAttributeBottom):
            bg.addConstraint_(
                NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                    scroll, attr, NSLayoutRelationEqual, bg, attr, 1.0, 0.0
                )
            )

        # Collection view in clip view
        self.collectionView = NSCollectionView.alloc().init()
        self.collectionView.setBackgroundColors_([NSColor.clearColor()])
        self.collectionView.setTranslatesAutoresizingMaskIntoConstraints_(False)
        clip = NSClipView.alloc().init()
        clip.setBackgroundColor_(NSColor.clearColor())
        clip.setDocumentView_(self.collectionView)
        scroll.setContentView_(clip)

        # ---- Prefer modern list layout; fall back if unavailable ----
        if NSCollectionLayoutListConfiguration and NSCollectionViewCompositionalLayout:
            # .sidebar = 1, .supplementary = 1 (enum ints used for bridge safety)
            config = NSCollectionLayoutListConfiguration.alloc().initWithAppearance_(1)
            config.setHeaderMode_(1)
            layout = NSCollectionViewCompositionalLayout.listWithConfiguration_(config)
        else:
            layout = NSCollectionViewFlowLayout.alloc().init()
        self.collectionView.setCollectionViewLayout_(layout)

        # Register item class (list cell if present, else generic item)
        itemClass = NSCollectionViewListCell or NSCollectionViewItem
        self.collectionView.registerClass_forItemWithIdentifier_(itemClass, CellID)
        # Section headers are optional; register a plain NSView for safety
        self.collectionView.registerClass_forSupplementaryViewOfKind_withIdentifier_(
            NSView, NSCollectionViewElementKindSectionHeader, HeaderID
        )

        self.collectionView.setDataSource_(self)
        self.collectionView.setDelegate_(self)
        self.collectionView.setSelectable_(True)

        # Data
        notes = generate_notes(32)
        self._sections = [[] for _ in range(4)]
        for note in sorted(notes, key=lambda n: n.date, reverse=True):
            self._sections[bucket(note.date)].append(note)

    # ---------- Data source ----------
    def numberOfSectionsInCollectionView_(self, cv):
        return len(self._sections)

    def collectionView_numberOfItemsInSection_(self, cv, section):
        return len(self._sections[section])

    def collectionView_itemForRepresentedObjectAtIndexPath_(self, cv, indexPath):
        item = cv.makeItemWithIdentifier_forIndexPath_(CellID, indexPath)
        note = self._sections[indexPath.section()][indexPath.item()]
        # If it's a real List Cell (Big Sur+), use defaultContentConfiguration
        if hasattr(item, "defaultContentConfiguration"):
            try:
                content = item.defaultContentConfiguration()
                content.setText_(note.title)
                content.setSecondaryText_(note.snippet)
                item.setContentConfiguration_(content)
                return item
            except Exception:
                pass  # fall through to manual label

        # Fallback: simple label inside item.view()
        v = item.view()
        if not v.subviews():
            title = NSTextField.labelWithString_("")
            title.setTranslatesAutoresizingMaskIntoConstraints_(False)
            v.addSubview_(title)
            for attr, const in ((NSLayoutAttributeLeading, 12.0),
                                (NSLayoutAttributeTop, 8.0)):
                v.addConstraint_(
                    NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                        title, attr, NSLayoutRelationEqual, v, attr, 1.0, const
                    )
                )
            item._titleLabel = title
        item._titleLabel.setStringValue_(note.title)
        return item

    # Section headers (works in both modes)
    def collectionView_viewForSupplementaryElementOfKind_atIndexPath_(self, cv, kind, indexPath):
        view = cv.makeSupplementaryViewOfKind_withIdentifier_forIndexPath_(kind, HeaderID, indexPath)
        if not view.subviews():
            label = NSTextField.labelWithString_("")
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)
            try:
                from AppKit import NSFont, NSColor
                label.setFont_(NSFont.boldSystemFontOfSize_(11))
                label.setTextColor_(NSColor.secondaryLabelColor())
            except Exception:
                pass
            view.addSubview_(label)
            for attr, const in ((NSLayoutAttributeLeading, 12.0),
                                (NSLayoutAttributeTop, 6.0),
                                (NSLayoutAttributeBottom, 3.0)):
                view.addConstraint_(
                    NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                        label, attr, NSLayoutRelationEqual, view, attr, 1.0, const
                    )
                )
            view._label = label
        view._label.setStringValue_(SECTIONS[indexPath.section()])
        return view

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, _):
        style = (NSWindowStyleMaskTitled | NSWindowStyleMaskClosable |
                 NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100, 100, 320, 600), style, 2, False
        )
        self.window.setTitle_("Notes-style Sidebar (PyObjC safe)")
        self.vc = ViewController.alloc().init()
        self.window.setContentViewController_(self.vc)
        self.window.makeKeyAndOrderFront_(None)

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
