from Cocoa import NSApplication, NSWindowController, NSTextField, NSApp
from objc import IBOutlet, IBAction
import os
from Foundation import NSURL, NSData
from Cocoa import NSNib
from Cocoa import NSObject

class AppDelegate(NSObject):
    pass  # or implement methods if needed

class SimpleXibDemoController(NSWindowController):
    window = IBOutlet()
    downloadButton = IBOutlet()
    logTextView = IBOutlet()
    sidebarCollectionView = IBOutlet()
    spinnerLoader = IBOutlet()
    statusLabel = IBOutlet()
    urlTextField = IBOutlet()

    def windowDidLoad(self):
        NSWindowController.windowDidLoad(self)
        self.window.makeKeyAndOrderFront_(None)

    @IBAction
    def urlTextFieldAction_(self, sender):
        self.spinnerLoader.stopAnimation_(self)
        self.statusLabel.setStringValue_(sender.stringValue())
        self.logTextView.setString_("URL Entered: " + sender.stringValue())
        self.downloadButton.setEnabled_(not self.downloadButton.isEnabled())

    @IBAction
    def downloadButtonAction_(self, sender):
        self.spinnerLoader.startAnimation_(self)
        self.statusLabel.setStringValue_("Downloading... " + self.urlTextField.stringValue())
        self.logTextView.setString_("Downloading... " + self.urlTextField.stringValue())

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    
    # controller allocated before nib instantiation
    controller = SimpleXibDemoController.alloc().initWithWindow_(None)

    xib_path = os.path.join(os.path.dirname(__file__), "MainMenu.nib")
    data = NSData.dataWithContentsOfURL_(NSURL.fileURLWithPath_(xib_path))
    if data is None:
        raise FileNotFoundError(xib_path)

    # Pass None for bundle if your nib doesn't reference external bundle resources
    nib = NSNib.alloc().initWithNibData_bundle_(data, None)
    ok, _ = nib.instantiateWithOwner_topLevelObjects_(controller, None)
    if not ok:
        raise RuntimeError("Failed to instantiate MainMenu.nib from data")

    controller.showWindow_(None)

    # Bring app to top
    NSApp.activateIgnoringOtherApps_(True)
    
    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()