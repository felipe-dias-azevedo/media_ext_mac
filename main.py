import os
from Foundation import NSBundle

# when running inside the .app bundle, the ffmpeg binary will be in Resources/ffmpeg
bundle = NSBundle.mainBundle()
if bundle and bundle.resourcePath():
    bundled_ffmpeg = os.path.join(bundle.resourcePath(), "ffmpeg")
    if os.path.exists(bundled_ffmpeg):
        os.environ["IMAGEIO_FFMPEG_EXE"] = bundled_ffmpeg

from Cocoa import (
    NSObject, NSApplication, NSWindow, NSTextField, NSScrollView,
    NSTextView, NSButton, NSMakeRect, NSMenu, NSMenuItem
)
from AppKit import (
    NSApplicationActivationPolicyRegular,
    NSToolbar,
    NSToolbarDisplayModeIconAndLabel,
    NSWindowStyleMaskTitled, NSWindowStyleMaskClosable, NSWindowStyleMaskResizable,
    NSBackingStoreBuffered,
    NSViewWidthSizable, NSViewHeightSizable, NSMakeSize,
    NSProgressIndicator, NSProgressIndicatorStyleSpinning,
    NSModalResponseOK
)
from AppKit import NSSavePanel, NSAlert 
from downloader import download, move_file
import threading

TOP_PAD = 20
SIDE_PAD = 20
BOTTOM_PAD = 20
ROW_H = 24
GAP = 12
BTN_W = 100
SPACING = 10              # gap between input and button
SPINNER_SPACING = 8       # gap between button and spinner
INPUT_MIN_W = 80          # minimum input width for usability
SPINNER_SIZE = 16         # classic small spinner size

class DownloaderLogger:
    def __init__(self, handler):
        self.content = ""
        self.handler = handler

    def output(self, text):
        self.content += text + "\n"

        print(text)
        # handler is expected to schedule UI updates on the main thread
        self.handler(self.content)

    def debug(self, msg):
        self.output(f"{msg}")

    def info(self, msg):
        self.output(f"[INFO] {msg}")

    def warning(self, msg):
        self.output(f"[WARNING] {msg}")

    def error(self, msg):
        self.output(f"[ERROR] {msg}")

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        # Build a minimal menu bar so standard Edit shortcuts work (Cmd+C/V/A)
        try:
            self._build_menus()
        except Exception:
            pass

        # Window
        style = (NSWindowStyleMaskTitled |
                 NSWindowStyleMaskClosable |
                 NSWindowStyleMaskResizable)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(100, 100, 720, 480), style, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("Media Extractor")
        # Ensure the top row always fits (input + button + spinner)
        min_w = SIDE_PAD + INPUT_MIN_W + SPACING + BTN_W + SPINNER_SPACING + SPINNER_SIZE + SIDE_PAD
        # increase minimum content height to match larger window
        self.window.setContentMinSize_(NSMakeSize(min_w, 360))
        # Add a toolbar
        toolbar = NSToolbar.alloc().initWithIdentifier_("mainToolbar")
        # We want the toolbar to show only the title by default; include a sidebar toggle item
        toolbar.setDisplayMode_(NSToolbarDisplayModeIconAndLabel)
        toolbar.setAllowsUserCustomization_(False)
        toolbar.setAutosavesConfiguration_(False)
        toolbar.setDelegate_(self)
        self.window.setToolbar_(toolbar)
        self.window.makeKeyAndOrderFront_(None)

        content = self.window.contentView()

        # Button (fixed width)
        self.button = NSButton.alloc().initWithFrame_(NSMakeRect(0, 0, BTN_W, ROW_H))
        self.button.setTitle_("Submit")
        self.button.setTarget_(self)
        self.button.setAction_("submitClicked:")
        content.addSubview_(self.button)

        # Input (resizes horizontally)
        self.input = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 300, ROW_H))
        self.input.setTarget_(self)
        self.input.setAction_("submitClicked:")
        self.input.setPlaceholderString_("Type URL")
        content.addSubview_(self.input)

        # Spinner (native macOS, always spinning)
        self.spinner = NSProgressIndicator.alloc().initWithFrame_(
            NSMakeRect(0, 0, SPINNER_SIZE, SPINNER_SIZE)
        )
        self.spinner.setStyle_(NSProgressIndicatorStyleSpinning)
        self.spinner.setIndeterminate_(True)
        # Don't show when stopped; we will start/stop it explicitly during downloads
        self.spinner.setDisplayedWhenStopped_(False)
        if hasattr(self.spinner, "setUsesThreadedAnimation_"):
            self.spinner.setUsesThreadedAnimation_(True)
        content.addSubview_(self.spinner)
        self.spinner.stopAnimation_(None)

        # Log (scrollable) — grows with window
        self.scroll = NSScrollView.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        self.scroll.setHasVerticalScroller_(True)
        self.scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)

        self.textview = NSTextView.alloc().initWithFrame_(self.scroll.contentView().bounds())
        self.textview.setEditable_(False)
        self.textview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        self.scroll.setDocumentView_(self.textview)
        content.addSubview_(self.scroll)

        # Logger: provide a handler that schedules UI updates on the main thread
        self.logger = DownloaderLogger(self._enqueue_log)

        # Handle window resize
        self.window.setDelegate_(self)
        self._layout()

        # Dock visibility
        NSApplication.sharedApplication()\
            .setActivationPolicy_(NSApplicationActivationPolicyRegular)\
            .activateIgnoringOtherApps_(True)

    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        # Make the app quit when the window is closed
        return True

    def _build_menus(self):
        # Create the main menu bar
        mainMenu = NSMenu.alloc().init()

        # Application menu (first, typically contains Quit)
        appMenuItem = NSMenuItem.alloc().init()
        appMenu = NSMenu.alloc().initWithTitle_("App")
        quitTitle = "Quit " + NSApplication.sharedApplication().applicationName() if hasattr(NSApplication.sharedApplication(), 'applicationName') else "Quit"
        quitItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(quitTitle, "terminate:", "q")
        appMenu.addItem_(quitItem)
        appMenuItem.setSubmenu_(appMenu)
        mainMenu.addItem_(appMenuItem)

        # Edit menu with standard Cut/Copy/Paste/Select All
        editMenuItem = NSMenuItem.alloc().init()
        editMenu = NSMenu.alloc().initWithTitle_("Edit")
        cutItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Cut", "cut:", "x")
        copyItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Copy", "copy:", "c")
        pasteItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Paste", "paste:", "v")
        selectAllItem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Select All", "selectAll:", "a")
        editMenu.addItem_(cutItem)
        editMenu.addItem_(copyItem)
        editMenu.addItem_(pasteItem)
        editMenu.addItem_(selectAllItem)
        editMenuItem.setSubmenu_(editMenu)
        mainMenu.addItem_(editMenuItem)

        NSApplication.sharedApplication().setMainMenu_(mainMenu)

    # Layout everything (no overlap; spinner right of button; input resizes)
    def _layout(self):
        content = self.window.contentView()
        cw = content.frame().size.width
        ch = content.frame().size.height

        row_y = ch - TOP_PAD - ROW_H

        # Button at top-right, leaving room for spinner
        btn_x = cw - SIDE_PAD - BTN_W - SPINNER_SPACING - SPINNER_SIZE
        btn_x = max(btn_x, SIDE_PAD + INPUT_MIN_W + SPACING)  # keep input >= min width
        self.button.setFrame_(NSMakeRect(btn_x, row_y, BTN_W, ROW_H))

        # Spinner to the right of button, vertically centered in the row
        spin_x = btn_x + BTN_W + SPINNER_SPACING
        spin_y = row_y + (ROW_H - SPINNER_SIZE) / 2.0
        self.spinner.setFrame_(NSMakeRect(spin_x, spin_y, SPINNER_SIZE, SPINNER_SIZE))

        # Input fills space to the left of the button
        max_input_w = btn_x - SPACING - SIDE_PAD
        input_w = max(INPUT_MIN_W, max_input_w)
        self.input.setFrame_(NSMakeRect(SIDE_PAD, row_y, input_w, ROW_H))

        # Scroll view below the row (only this grows)
        scroll_top = row_y - GAP
        scroll_h = max(0, scroll_top - BOTTOM_PAD)
        self.scroll.setFrame_(NSMakeRect(SIDE_PAD, BOTTOM_PAD, cw - 2 * SIDE_PAD, scroll_h))

    def windowDidResize_(self, _):
        self._layout()

    def _enqueue_log(self, text):
        # Schedule appendLog_: on the main thread (performSelector name ends with ':')
        self.performSelectorOnMainThread_withObject_waitUntilDone_("appendLog:", text, False)

    def appendLog_(self, text):
        # This runs on the main thread
        self.textview.setString_(text)

    def submitClicked_(self, sender):
        text = self.input.stringValue().strip()
        if not text:
            return

        # Validate URL
        if not text.lower().startswith("https://"):
            alert = NSAlert.alloc().init()
            alert.setMessageText_("Invalid URL")
            alert.setInformativeText_("Please enter a valid URL.")
            alert.addButtonWithTitle_("OK")
            alert.runModal()
            return

        self.logger.info(f"Starting download for URL: {text}")
        # Disable UI and show spinner, then run download in background thread
        self.setBusy_(True)
        threading.Thread(target=self._download_thread, args=(text,), daemon=True).start()

    def _download_thread(self, url):
        try:
            path = download(url, self.logger)
            self.logger.info(f"Download finished successfully: {path}")
            
            self.performSelectorOnMainThread_withObject_waitUntilDone_("presentSavePanelForPath:", path, True)

        except Exception as e:
            self.logger.error(f"Download failed: {e}")
        finally:
            self.performSelectorOnMainThread_withObject_waitUntilDone_("setBusy:", False, False)

    def setBusy_(self, is_busy):

        self.button.setEnabled_(not is_busy)
        self.input.setEnabled_(not is_busy)
        self.input.setEditable_(not is_busy)

        if is_busy:
            self.spinner.startAnimation_(None)
        else:
            self.spinner.stopAnimation_(None)
            self.input.setStringValue_("")

    def presentSavePanelForPath_(self, src_path):

        save_path = self.openSavePanel_(src_path)
        while save_path is None:
            save_path = self.openSavePanel_(src_path)

        self.logger.info(f"Saving to: {save_path}")

        move_file(src_path, save_path)

        self.logger.info("File saved successfully.")

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


if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    app.activateIgnoringOtherApps_(True)
    app.run()
