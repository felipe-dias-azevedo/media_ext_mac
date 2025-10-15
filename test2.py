import os
import sys
from Foundation import NSURL
from AppKit import (NSApplication, NSApp, NSNib,
                    NSWindowController)
from PyObjCTools import AppHelper

class SimpleXibDemoController(NSWindowController):
    def init(self):
        self = super(SimpleXibDemoController, self).initWithWindow_(None)
        return self

def main():
    # Register class before loading nib
    _ = SimpleXibDemoController

    NSApplication.sharedApplication()

    # Load MainMenu.xib that sits next to this script
    here = os.path.dirname(os.path.abspath(__file__))
    nib_url = NSURL.fileURLWithPath_(os.path.join(here, "MainMenu.xib"))

    # Owner can be NSApp or a controller; using NSApp is fine for MainMenu.xib
    nib = NSNib.alloc().initWithContentsOfURL_(nib_url)
    ok, top = nib.instantiateWithOwner_topLevelObjects_(NSApp, None)
    if not ok:
        raise RuntimeError("Failed to instantiate MainMenu.xib")

    # Create your window controller and show the window
    controller = SimpleXibDemoController.alloc().init()
    controller.showWindow_(None)

    # Keep a strong ref so it isn’t GC’d
    NSApp.delegate = controller

    AppHelper.runEventLoop()

if __name__ == "__main__":
    main()
