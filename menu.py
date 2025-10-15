from Cocoa import (
    NSApplication, NSApp, NSWindow, NSMenu, NSMenuItem, NSTextView
)
import objc

def buildMenus():
    main = NSMenu.alloc().init()

    # App
    appItem = NSMenuItem.alloc().init()
    appMenu = NSMenu.alloc().init()
    about = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("About MediaExtSwiftUI",
                                                                    objc.selector(NSApp.orderFrontStandardAboutPanel_, signature=b"v@:@"),
                                                                    "")
    about.setTarget_(NSApp)
    appMenu.addItem_(about)
    appMenu.addItem_(NSMenuItem.separatorItem())
    appMenu.addItemWithTitle_action_keyEquivalent_("Preferences…", None, ",")
    appMenu.addItem_(NSMenuItem.separatorItem())
    appMenu.addItemWithTitle_action_keyEquivalent_("Quit MediaExtSwiftUI",
                                                    objc.selector(NSApp.terminate_, signature=b"v@:@"),
                                                    "q")
    appItem.setSubmenu_(appMenu)
    main.addItem_(appItem)

    # File
    fileItem = NSMenuItem.alloc().init()
    fileMenu = NSMenu.alloc().initWithTitle_("File")
    fileMenu.addItemWithTitle_action_keyEquivalent_("Close Window",
                                                    objc.selector(NSWindow.performClose_, signature=b"v@:@"),
                                                    "w")
    fileItem.setSubmenu_(fileMenu)
    main.addItem_(fileItem)

    # Edit
    editItem = NSMenuItem.alloc().init()
    editMenu = NSMenu.alloc().initWithTitle_("Edit")
    editMenu.addItemWithTitle_action_keyEquivalent_("Cut", objc.selector(NSTextView.cut_, signature=b"v@:@"), "x")
    editMenu.addItemWithTitle_action_keyEquivalent_("Copy", objc.selector(NSTextView.copy_, signature=b"v@:@"), "c")
    editMenu.addItemWithTitle_action_keyEquivalent_("Paste", objc.selector(NSTextView.paste_, signature=b"v@:@"), "v")
    editMenu.addItemWithTitle_action_keyEquivalent_("Select All", objc.selector(NSTextView.selectAll_, signature=b"v@:@"), "a")
    editItem.setSubmenu_(editMenu)
    main.addItem_(editItem)

    # Window
    winItem = NSMenuItem.alloc().init()
    winMenu = NSMenu.alloc().initWithTitle_("Window")
    winMenu.addItemWithTitle_action_keyEquivalent_("Minimize", objc.selector(NSWindow.performMiniaturize_, signature=b"v@:@"), "m")
    winMenu.addItemWithTitle_action_keyEquivalent_("Zoom", objc.selector(NSWindow.performZoom_, signature=b"v@:@"), "")
    winMenu.addItem_(NSMenuItem.separatorItem())
    winMenu.addItemWithTitle_action_keyEquivalent_("Bring All to Front", objc.selector(NSApplication.arrangeInFront_, signature=b"v@:@"), "")
    winItem.setSubmenu_(winMenu)
    main.addItem_(winItem)
    NSApp.setWindowsMenu_(winMenu)

    # Help
    helpItem = NSMenuItem.alloc().init()
    helpMenu = NSMenu.alloc().initWithTitle_("Help")
    helpMenu.addItemWithTitle_action_keyEquivalent_("MediaExtSwiftUI Help", None, "?")
    helpItem.setSubmenu_(helpMenu)
    main.addItem_(helpItem)

    NSApp.setMainMenu_(main)