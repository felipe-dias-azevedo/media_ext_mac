import objc
from Cocoa import (
    NSView, NSWindow, NSWindowController, NSWindowStyleMaskTitled,
    NSWindowStyleMaskClosable, NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskResizable, NSBackingStoreBuffered,
    NSMakeRect, NSColor, NSLayoutConstraint,
    NSApp, NSMakeSize
)
from log_viewer import LogViewer

class DownloaderLogger:
    def __init__(self, handler):
        self.content = ""
        self.handler = handler

    def output(self, text):
        self.content += text + "\n"

        if "--dev" in __import__("sys").argv:
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


class LogWindowController(NSWindowController):
    shared = None

    @classmethod
    def sharedController(cls):
        if cls.shared is None:
            cls.shared = cls.alloc().init()
        return cls.shared

    def init(self):
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 540, 420),
            (NSWindowStyleMaskTitled |
             NSWindowStyleMaskClosable |
             NSWindowStyleMaskResizable),
            NSBackingStoreBuffered,
            False,
        )
        win.setTitle_("Logs")
        win.center()
        win.setContentMinSize_(NSMakeSize(320, 210))

        content = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 540, 420))
        content.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.logViewer = LogViewer.alloc().init()
        self.logViewer.setTranslatesAutoresizingMaskIntoConstraints_(False)
        content.addSubview_(self.logViewer)

        NSLayoutConstraint.activateConstraints_([
            self.logViewer.leadingAnchor().constraintEqualToAnchor_(content.leadingAnchor()),
            self.logViewer.trailingAnchor().constraintEqualToAnchor_(content.trailingAnchor()),
            self.logViewer.topAnchor().constraintEqualToAnchor_(content.topAnchor()),
            self.logViewer.bottomAnchor().constraintEqualToAnchor_(content.bottomAnchor()),
        ])

        win.setContentView_(content)

        self = objc.super(LogWindowController, self).initWithWindow_(win)
        if self is None:
            return None

        self.logger = DownloaderLogger(self.enqueue_log)

        return self

    def enqueue_log(self, text):
        if self.window() is None:
            return
        self.performSelectorOnMainThread_withObject_waitUntilDone_("appendLog:", text, False)

    def appendLog_(self, text):
        self.logViewer.appendLog_(text)

    def showWindow_(self, sender):
        if self.window() is None:
            return
        if self.window().isVisible():
            self.window().makeKeyAndOrderFront_(sender)
        else:
            objc.super(LogWindowController, self).showWindow_(sender)
        NSApp.activateIgnoringOtherApps_(True)
