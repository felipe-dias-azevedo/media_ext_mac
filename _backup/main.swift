// main.swift
import AppKit

// MARK: - Models

struct MediaItem {
    let title: String
    let timestamp: String
    let isGroup: Bool
    init(groupTitle: String) { self.title = groupTitle; self.timestamp = ""; self.isGroup = true }
    init(title: String, timestamp: String) { self.title = title; self.timestamp = timestamp; self.isGroup = false }
}

// MARK: - Sidebar

final class SidebarVC: NSViewController, NSTableViewDataSource, NSTableViewDelegate {
    private let table = NSTableView()
    private let scroll = NSScrollView()
    private var data: [MediaItem] = [
        .init(groupTitle: "January"),
        .init(title: "o-astronauta-de-marmore.mp3", timestamp: "13/10/25, 16:24:20"),
        .init(title: "voce-nao-me-ensinou-a-te-esquecer.mp3", timestamp: "13/10/25, 16:24:20"),
        .init(title: "test.mp3", timestamp: "13/10/25, 16:24:36"),
        .init(title: "test.mp3", timestamp: "13/10/25, 16:25:21")
    ]

    override func loadView() {
        view = NSView()
        scroll.documentView = table
        scroll.hasVerticalScroller = true
        table.headerView = nil
        table.rowHeight = 48
        table.intercellSpacing = NSSize(width: 0, height: 0)
        table.style = .inset
        table.backgroundColor = .windowBackgroundColor

        let col = NSTableColumn(identifier: .init("main"))
        table.addTableColumn(col)
        table.delegate = self
        table.dataSource = self

        view.addSubview(scroll)
        scroll.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            scroll.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scroll.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scroll.topAnchor.constraint(equalTo: view.topAnchor),
            scroll.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])
    }

    func numberOfRows(in tableView: NSTableView) -> Int { data.count }
    func tableView(_ tableView: NSTableView, isGroupRow row: Int) -> Bool { data[row].isGroup }

    func tableView(_ tableView: NSTableView, viewFor tableColumn: NSTableColumn?, row: Int) -> NSView? {
        let item = data[row]
        if item.isGroup {
            let v = NSTableCellView()
            let label = NSTextField(labelWithString: item.title)
            label.font = .systemFont(ofSize: NSFont.systemFontSize, weight: .semibold)
            label.textColor = .secondaryLabelColor
            v.addSubview(label)
            label.translatesAutoresizingMaskIntoConstraints = false
            NSLayoutConstraint.activate([
                label.leadingAnchor.constraint(equalTo: v.leadingAnchor, constant: 12),
                label.centerYAnchor.constraint(equalTo: v.centerYAnchor)
            ])
            return v
        } else {
            let v = NSTableCellView()
            let title = NSTextField(labelWithString: item.title)
            title.font = .systemFont(ofSize: 12, weight: .medium)
            title.lineBreakMode = .byTruncatingMiddle
            let sub = NSTextField(labelWithString: item.timestamp)
            sub.font = .systemFont(ofSize: 10)
            sub.textColor = .secondaryLabelColor
            v.addSubview(title); v.addSubview(sub)
            title.translatesAutoresizingMaskIntoConstraints = false
            sub.translatesAutoresizingMaskIntoConstraints = false
            NSLayoutConstraint.activate([
                title.leadingAnchor.constraint(equalTo: v.leadingAnchor, constant: 12),
                title.trailingAnchor.constraint(equalTo: v.trailingAnchor, constant: -12),
                title.topAnchor.constraint(equalTo: v.topAnchor, constant: 6),
                sub.leadingAnchor.constraint(equalTo: title.leadingAnchor),
                sub.trailingAnchor.constraint(equalTo: title.trailingAnchor),
                sub.topAnchor.constraint(equalTo: title.bottomAnchor, constant: 0),
                sub.bottomAnchor.constraint(equalTo: v.bottomAnchor, constant: -6)
            ])
            return v
        }
    }
}

// MARK: - Status pill

final class StatusPill: NSView {
    private let box = NSBox()
    private let icon = NSImageView()
    private let spinner = NSProgressIndicator()
    private let label = NSTextField(labelWithString: "")

    enum Kind { case success(String), progress(String) }

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        box.boxType = .custom
        box.cornerRadius = 8
        box.borderWidth = 0.5
        box.borderColor = .separatorColor
        box.fillColor = .controlBackgroundColor
        addSubview(box)

        icon.symbolConfiguration = .init(pointSize: 14, weight: .semibold)
        icon.contentTintColor = .systemGreen
        spinner.style = .spinning
        spinner.controlSize = .small
        spinner.isDisplayedWhenStopped = false
        label.font = .systemFont(ofSize: 13, weight: .medium)

        let stack = NSStackView(views: [icon, spinner, label])
        stack.orientation = .horizontal
        stack.spacing = 8
        stack.alignment = .centerY
        addSubview(stack)

        [box, stack].forEach { $0.translatesAutoresizingMaskIntoConstraints = false }
        NSLayoutConstraint.activate([
            box.leadingAnchor.constraint(equalTo: leadingAnchor),
            box.trailingAnchor.constraint(equalTo: trailingAnchor),
            box.topAnchor.constraint(equalTo: topAnchor),
            box.bottomAnchor.constraint(equalTo: bottomAnchor),

            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(lessThanOrEqualTo: trailingAnchor, constant: -16),
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 8),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -8)
        ])
        set(.success("Success"))
    }

    required init?(coder: NSCoder) { fatalError() }

    func set(_ kind: Kind) {
        switch kind {
        case .success(let msg):
            spinner.stopAnimation(nil)
            spinner.isHidden = true
            icon.isHidden = false
            icon.image = NSImage(systemSymbolName: "checkmark", accessibilityDescription: nil)
            label.stringValue = msg
            label.textColor = .systemGreen
        case .progress(let msg):
            icon.isHidden = true
            spinner.isHidden = false
            spinner.startAnimation(nil)
            label.stringValue = msg
            label.textColor = .labelColor
        }
    }
}

// MARK: - Right content

final class ContentVC: NSViewController {
    override func viewDidAppear() {
        super.viewDidAppear()
        extractButton.keyEquivalent = "\r"
        view.window?.defaultButtonCell = extractButton.cell as? NSButtonCell
    }

    // URL box
    private let urlContainer = NSView()
    private let urlInlineLabel = NSTextField(labelWithString: "URL")
    private let urlField: NSTextField = {
        let tf = NSTextField()
        tf.isBordered = false
        tf.drawsBackground = false
        tf.focusRingType = .none
        tf.placeholderString = "https"
        tf.lineBreakMode = .byTruncatingMiddle
        tf.cell?.wraps = false
        tf.cell?.isScrollable = true
        tf.cell?.usesSingleLineMode = true
        tf.maximumNumberOfLines = 1
        return tf
    }()
    private let pasteButton: NSButton = {
        let b = NSButton()
        b.isBordered = false
        b.bezelStyle = .shadowlessSquare
        b.image = NSImage(systemSymbolName: "doc.on.clipboard", accessibilityDescription: "Paste")
        b.imagePosition = .imageOnly
        b.setButtonType(.momentaryPushIn)
        b.toolTip = "Paste"
        return b
    }()

    // Extract button
    private let extractButton: NSButton = {
        let b = NSButton(title: "Extract", target: nil, action: nil)
        b.isBordered = true
        b.bezelStyle = .rounded
        b.setButtonType(.momentaryPushIn)
        b.toolTip = "Extract"
        b.controlSize = .large
        let attr = NSMutableAttributedString(string: "Extract")
        attr.addAttributes([
            .foregroundColor: NSColor.controlTextColor,
            .font: NSFont.systemFont(ofSize: 13, weight: .semibold)
        ], range: NSRange(location: 0, length: attr.length))
        b.attributedTitle = attr
        b.setContentHuggingPriority(.required, for: .horizontal)
        b.setContentCompressionResistancePriority(.required, for: .horizontal)
        return b
    }()

    private let status = StatusPill()

    // Logs: use Apple's pre-configured scrollable plain text view
    private let logScroll: NSScrollView = NSTextView.scrollablePlainDocumentContentTextView()
    private lazy var logText: NSTextView = {
        // Safe to force-cast; factory always supplies an NSTextView
        let tv = logScroll.documentView as! NSTextView
        return tv
    }()

    override func loadView() {
        view = NSView()

        // URL container look
        urlContainer.wantsLayer = true
        urlContainer.layer?.cornerRadius = 8
        urlContainer.layer?.borderWidth = 0.5
        urlContainer.layer?.borderColor = NSColor.separatorColor.cgColor
        urlContainer.layer?.backgroundColor = NSColor.controlBackgroundColor.cgColor

        urlInlineLabel.font = .systemFont(ofSize: 12, weight: .semibold)
        urlInlineLabel.textColor = .secondaryLabelColor

        // Configure the text view (already embedded correctly in logScroll)
        logText.isEditable = false
        logText.isSelectable = true
        logText.isRichText = false
        logText.usesFindBar = true
        logText.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        logText.textColor = .labelColor
        logText.drawsBackground = false
        logText.textContainerInset = NSSize(width: 10, height: 10)
        logText.string = "teste" // initial content shows immediately

        // Make sure wrapping and growth are correct (factory sets most of this)
        logText.isHorizontallyResizable = false
        logText.isVerticallyResizable = true
        logText.autoresizingMask = [.width]
        if let tc = logText.textContainer {
            tc.widthTracksTextView = true
            tc.containerSize = NSSize(width: logScroll.contentSize.width,
                                      height: .greatestFiniteMagnitude)
        }

        // Scroll view look
        logScroll.hasVerticalScroller = true
        logScroll.borderType = .noBorder
        logScroll.drawsBackground = false
        logScroll.translatesAutoresizingMaskIntoConstraints = false

        // Logs container look
        let logContainer = NSView()
        logContainer.wantsLayer = true
        logContainer.layer?.cornerRadius = 8
        logContainer.layer?.borderWidth = 0.5
        logContainer.layer?.borderColor = NSColor.separatorColor.cgColor
        logContainer.layer?.backgroundColor = NSColor.controlBackgroundColor.cgColor
        logContainer.translatesAutoresizingMaskIntoConstraints = false
        logContainer.addSubview(logScroll)

        // Layout: outer
        [urlContainer, extractButton, status, logContainer].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview($0)
        }
        // Layout: url inner
        [urlInlineLabel, urlField, pasteButton].forEach {
            $0.translatesAutoresizingMaskIntoConstraints = false
            urlContainer.addSubview($0)
        }

        // Priorities
        extractButton.setContentHuggingPriority(.required, for: .horizontal)
        extractButton.setContentCompressionResistancePriority(.required, for: .horizontal)
        urlField.setContentHuggingPriority(.defaultLow, for: .horizontal)
        urlField.setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
        pasteButton.setContentHuggingPriority(.required, for: .horizontal)
        pasteButton.setContentCompressionResistancePriority(.required, for: .horizontal)

        if #unavailable(macOS 13.0) {
            extractButton.widthAnchor.constraint(greaterThanOrEqualToConstant: 84).isActive = true
        }

        NSLayoutConstraint.activate([
            // URL box
            urlContainer.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 24),
            urlContainer.topAnchor.constraint(equalTo: view.topAnchor, constant: 16),
            urlContainer.trailingAnchor.constraint(equalTo: extractButton.leadingAnchor, constant: -12),
            urlContainer.heightAnchor.constraint(equalToConstant: 30),

            urlInlineLabel.leadingAnchor.constraint(equalTo: urlContainer.leadingAnchor, constant: 10),
            urlInlineLabel.centerYAnchor.constraint(equalTo: urlContainer.centerYAnchor),

            urlField.leadingAnchor.constraint(equalTo: urlInlineLabel.trailingAnchor, constant: 10),
            urlField.centerYAnchor.constraint(equalTo: urlContainer.centerYAnchor),
            urlField.trailingAnchor.constraint(equalTo: pasteButton.leadingAnchor, constant: -8),

            pasteButton.trailingAnchor.constraint(equalTo: urlContainer.trailingAnchor, constant: -10),
            pasteButton.centerYAnchor.constraint(equalTo: urlContainer.centerYAnchor),

            // Extract
            extractButton.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -24),
            extractButton.centerYAnchor.constraint(equalTo: urlContainer.centerYAnchor),
            extractButton.heightAnchor.constraint(equalToConstant: 20),

            // Status
            status.leadingAnchor.constraint(equalTo: urlContainer.leadingAnchor),
            status.trailingAnchor.constraint(equalTo: extractButton.trailingAnchor),
            status.topAnchor.constraint(equalTo: urlContainer.bottomAnchor, constant: 12),
            status.heightAnchor.constraint(greaterThanOrEqualToConstant: 32),

            // Logs container
            logContainer.leadingAnchor.constraint(equalTo: status.leadingAnchor),
            logContainer.trailingAnchor.constraint(equalTo: status.trailingAnchor),
            logContainer.topAnchor.constraint(equalTo: status.bottomAnchor, constant: 12),
            logContainer.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -20),

            // Scroll fills logs container
            logScroll.leadingAnchor.constraint(equalTo: logContainer.leadingAnchor),
            logScroll.trailingAnchor.constraint(equalTo: logContainer.trailingAnchor),
            logScroll.topAnchor.constraint(equalTo: logContainer.topAnchor),
            logScroll.bottomAnchor.constraint(equalTo: logContainer.bottomAnchor)
        ])

        // Button min width for padding
        let extraHorizontalPadding: CGFloat = 20
        let titleWidth = extractButton.attributedTitle.size().width
        let minButtonWidth = ceil(titleWidth + extraHorizontalPadding)
        extractButton.widthAnchor.constraint(greaterThanOrEqualToConstant: minButtonWidth).isActive = true

        // Actions
        pasteButton.target = self
        pasteButton.action = #selector(pasteURL)
        extractButton.target = self
        extractButton.action = #selector(extract(_:))
    }

    override func viewDidLayout() {
        super.viewDidLayout()
        // Keep wrapping width synced to the visible area
        if let tc = logText.textContainer {
            tc.containerSize = NSSize(width: logScroll.contentSize.width, height: .greatestFiniteMagnitude)
        }
    }

    @objc private func pasteURL() {
        if let str = NSPasteboard.general.string(forType: .string) {
            urlField.stringValue = str
        }
        status.set(.success("Success"))
    }

    private func appendLog(_ text: String) {
        DispatchQueue.main.async {
            if self.logText.string.isEmpty {
                self.logText.string = text
            } else {
                self.logText.string += "\n" + text
            }
            self.logText.layoutManager?.ensureLayout(for: self.logText.textContainer!)
            self.logText.scrollRangeToVisible(NSRange(location: self.logText.string.utf16.count, length: 0))
        }
    }

    @objc private func extract(_ sender: Any?) {
        status.set(.progress("Downloading"))
        appendLog("test\ntest\ntest")
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
            self.status.set(.success("Success"))
            self.appendLog("test\ntest\ntest")
        }
    }
}

// MARK: - Split container

final class RootSplitVC: NSSplitViewController {
    private let sidebar = SidebarVC()
    private let content = ContentVC()

    override func viewDidLoad() {
        super.viewDidLoad()
        minimumThicknessForInlineSidebars = 220
        let left = NSSplitViewItem(sidebarWithViewController: sidebar)
        left.minimumThickness = 220
        left.canCollapse = false
        let right = NSSplitViewItem(viewController: content)
        right.minimumThickness = 420
        addSplitViewItem(left)
        addSplitViewItem(right)
    }
}

// MARK: - App Delegate + Menus

final class AppDelegate: NSObject, NSApplicationDelegate, NSToolbarDelegate {
    var window: NSWindow!

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        buildMenus()

        let splitVC = RootSplitVC()
        window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 930, height: 520),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.center()
        window.title = "MediaExtSwiftUI"
        window.contentViewController = splitVC
        window.makeKeyAndOrderFront(nil)

        let tb = NSToolbar(identifier: "MainToolbar")
        tb.delegate = self
        tb.displayMode = .iconOnly
        window.toolbar = tb

        NSApp.activate(ignoringOtherApps: true)
    }

    private func buildMenus() {
        let main = NSMenu()

        // App
        let appItem = NSMenuItem()
        let app = NSMenu()
        let about = NSMenuItem(
            title: "About MediaExtSwiftUI",
            action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)),
            keyEquivalent: ""
        )
        about.target = NSApp
        app.addItem(about)
        app.addItem(.separator())
        app.addItem(withTitle: "Preferences…", action: nil, keyEquivalent: ",")
        app.addItem(.separator())
        app.addItem(withTitle: "Quit MediaExtSwiftUI", action: #selector(NSApp.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = app
        main.addItem(appItem)

        // File
        let fileItem = NSMenuItem()
        let file = NSMenu(title: "File")
        file.addItem(withTitle: "Close Window", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        fileItem.submenu = file
        main.addItem(fileItem)

        // Edit
        let editItem = NSMenuItem()
        let edit = NSMenu(title: "Edit")
        edit.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = edit
        main.addItem(editItem)

        // Window
        let winItem = NSMenuItem()
        let win = NSMenu(title: "Window")
        win.addItem(withTitle: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        win.addItem(withTitle: "Zoom", action: #selector(NSWindow.performZoom(_:)), keyEquivalent: "")
        win.addItem(.separator())
        win.addItem(withTitle: "Bring All to Front", action: #selector(NSApplication.arrangeInFront(_:)), keyEquivalent: "")
        winItem.submenu = win
        main.addItem(winItem)
        NSApp.windowsMenu = win

        // Help
        let helpItem = NSMenuItem()
        let help = NSMenu(title: "Help")
        help.addItem(withTitle: "MediaExtSwiftUI Help", action: nil, keyEquivalent: "?")
        helpItem.submenu = help
        main.addItem(helpItem)

        NSApp.mainMenu = main
    }

    func toolbarAllowedItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] { [.flexibleSpace] }
    func toolbarDefaultItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] { [.flexibleSpace] }
}

// MARK: - Bootstrap (no @main)

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
