from Cocoa import NSApplication, NSWindowController, NSTextField, NSApp
from objc import IBOutlet, IBAction

from Cocoa import NSObject

class AppDelegate(NSObject):
    pass  # or implement methods if needed

class SimpleXibDemoController(NSWindowController):
    counterTextField = IBOutlet()

    def windowDidLoad(self):
        NSWindowController.windowDidLoad(self)
        self.count = 0

    @IBAction
    def increment_(self, sender):
        self.count += 1
        self.updateDisplay()

    @IBAction
    def decrement_(self, sender):
        self.count -= 1
        self.updateDisplay()

    def updateDisplay(self):
        # NSTextField expects a string
        try:
            self.counterTextField.setStringValue_(str(self.count))
        except Exception:
            pass

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    
    # Initiate the controller with the XIB
    viewController = SimpleXibDemoController.alloc().initWithWindowNibName_("MainMenu")

    # Show the window (pass the window object)
    viewController.showWindow_(None)
    # viewController.showWindow_(viewController.window())
    
    NSApp.setDelegate_(viewController)

    # Bring app to top
    NSApp.activateIgnoringOtherApps_(True)
    
    from PyObjCTools import AppHelper
    AppHelper.runEventLoop()