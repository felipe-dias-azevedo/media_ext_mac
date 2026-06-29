from dataclasses import dataclass

import objc

from AppKit import (
    NSAnimationContext,
    NSLayoutAttributeCenterY,
    NSLayoutConstraint,
    NSBox,
    NSBoxSeparator,
    NSButton,
    NSColor,
    NSControlSizeSmall,
    NSControlSizeLarge,
    NSFont,
    NSFontWeightMedium,
    NSFontWeightSemibold,
    NSImage,
    NSImageSymbolConfiguration,
    NSImageView,
    NSLeftTextAlignment,
    NSMakeRect,
    NSMakeSize,
    NSProgressIndicator,
    NSProgressIndicatorStyleBar,
    NSProgressIndicatorStyleSpinning,
    NSScrollView,
    NSTextField,
    NSStackView,
    NSStackViewDistributionFill,
    NSStackViewGravityCenter,
    NSStackViewGravityLeading,
    NSUserInterfaceLayoutOrientationHorizontal,
    NSUserInterfaceLayoutOrientationVertical,
    NSView,
    NSVisualEffectView,
    NSVisualEffectMaterialHUDWindow,
    NSVisualEffectMaterialHeaderView,
    NSVisualEffectBlendingModeWithinWindow,
    NSVisualEffectStateActive,
    NSBoxCustom,
    NSLineBreakByTruncatingTail,
    NSWindowAbove,
    NSLayoutAttributeLeading
)
from utils.symbols import create_symbol
from views.current_step_separator_view import CurrentStepSeparator

# ============================================================
# Playlist Status
# ============================================================

@dataclass
class PlaylistItemStatus:
    id: str
    name: str
    action: str
    description: str | None = None


HEADER_HEIGHT = 44

class FlippedView(NSView):
    def isFlipped(self):
        return True

class PlaylistItemRowView(NSView):
    STATE_PENDING = "pending"
    STATE_LOADING = "loading"
    STATE_SUCCESS = "success"
    STATE_ERROR = "error"

    def init(self):
        self = objc.super(PlaylistItemRowView, self).init()
        if self is None:
            return None

        self.item_id = None
        self.state = self.STATE_PENDING

        self.iconView = NSImageView.alloc().init()

        self.spinner = NSProgressIndicator.alloc().init()
        self.spinner.setStyle_(NSProgressIndicatorStyleSpinning)
        self.spinner.setControlSize_(NSControlSizeSmall)
        self.spinner.setDisplayedWhenStopped_(False)

        self.titleLabel = NSTextField.labelWithString_("")
        self.titleLabel.setFont_(
            NSFont.systemFontOfSize_weight_(
                NSFont.systemFontSize(),
                NSFontWeightSemibold,
            )
        )
        self.titleLabel.setAlignment_(NSLeftTextAlignment)

        self.actionLabel = NSTextField.labelWithString_("")
        self.actionLabel.setFont_(NSFont.systemFontOfSize_(NSFont.smallSystemFontSize()))
        self.actionLabel.setTextColor_(NSColor.secondaryLabelColor())
        self.actionLabel.setAlignment_(NSLeftTextAlignment)

        self.descriptionLabel = NSTextField.labelWithString_("")
        self.descriptionLabel.setFont_(NSFont.systemFontOfSize_(NSFont.smallSystemFontSize()))
        self.descriptionLabel.setTextColor_(NSColor.secondaryLabelColor())
        self.descriptionLabel.setAlignment_(NSLeftTextAlignment)
        self.descriptionLabel.setLineBreakMode_(NSLineBreakByTruncatingTail)

        self.showFolderButton = NSButton.buttonWithTitle_target_action_("Show", self, "showFolderButtonClicked_:" )
        self.showFolderButton.setControlSize_(NSControlSizeSmall)
        self.showFolderButton.setBordered_(True)
        self.showFolderButton.setHidden_(True)
        self.showFolderButton.setEnabled_(False)

        self.textStack = NSStackView.stackViewWithViews_([
            self.titleLabel,
            self.actionLabel,
        ])
        self.textStack.setOrientation_(NSUserInterfaceLayoutOrientationVertical)
        self.textStack.setAlignment_(NSStackViewGravityLeading)
        self.textStack.setDistribution_(NSStackViewDistributionFill)
        self.textStack.setSpacing_(2)

        self.leadingContainer = NSView.alloc().init()
        self.leadingContainer.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.leadingContainer.addSubview_(self.iconView)
        self.leadingContainer.addSubview_(self.spinner)

        self.addSubview_(self.leadingContainer)
        self.addSubview_(self.textStack)
        self.addSubview_(self.descriptionLabel)
        self.addSubview_(self.showFolderButton)

        for view in (
            self.leadingContainer,
            self.iconView,
            self.spinner,
            self.textStack,
            self.descriptionLabel,
            self.showFolderButton,
        ):
            view.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([
            self.leadingContainer.leadingAnchor().constraintEqualToAnchor_constant_(self.leadingAnchor(), 10),
            self.leadingContainer.centerYAnchor().constraintEqualToAnchor_(self.centerYAnchor()),
            self.leadingContainer.widthAnchor().constraintEqualToConstant_(20),
            self.leadingContainer.heightAnchor().constraintEqualToConstant_(20),

            self.iconView.centerXAnchor().constraintEqualToAnchor_(self.leadingContainer.centerXAnchor()),
            self.iconView.centerYAnchor().constraintEqualToAnchor_(self.leadingContainer.centerYAnchor()),

            self.spinner.centerXAnchor().constraintEqualToAnchor_(self.leadingContainer.centerXAnchor()),
            self.spinner.centerYAnchor().constraintEqualToAnchor_(self.leadingContainer.centerYAnchor()),

            self.textStack.leadingAnchor().constraintEqualToAnchor_constant_(
                self.leadingContainer.trailingAnchor(),
                10,
            ),
            self.textStack.topAnchor().constraintEqualToAnchor_(
                self.topAnchor()
            ),
            self.textStack.bottomAnchor().constraintEqualToAnchor_(
                self.bottomAnchor()
            ),
            self.textStack.widthAnchor().constraintLessThanOrEqualToConstant_(260),

            self.showFolderButton.trailingAnchor().constraintEqualToAnchor_(
                self.trailingAnchor()
            ),
            self.showFolderButton.centerYAnchor().constraintEqualToAnchor_(
                self.centerYAnchor()
            ),

            self.descriptionLabel.leadingAnchor().constraintEqualToAnchor_constant_(
                self.textStack.trailingAnchor(),
                10,
            ),
            self.descriptionLabel.trailingAnchor().constraintEqualToAnchor_constant_(
                self.showFolderButton.leadingAnchor(),
                -10,
            ),
            self.descriptionLabel.centerYAnchor().constraintEqualToAnchor_(
                self.centerYAnchor()
            ),
        ])

        self.iconView.setHidden_(True)
        self.spinner.setHidden_(True)

        return self

    def configureWithId_name_action_(self, item_id, name, action):
        self.item_id = item_id
        self.titleLabel.setStringValue_(name or "")
        self.actionLabel.setStringValue_(action or "")
        self.descriptionLabel.setStringValue_("")
        self.showFolderButton.setHidden_(True)
        self.showFolderButton.setEnabled_(False)

    def setDescription_(self, description):
        if description:
            self.descriptionLabel.setStringValue_(description)
        else:
            self.descriptionLabel.setStringValue_("")

    def setPending(self):
        self.state = self.STATE_PENDING
        self.iconView.setHidden_(True)
        self.spinner.stopAnimation_(None)
        self.spinner.setHidden_(True)
        self.showFolderButton.setHidden_(True)
        self.showFolderButton.setEnabled_(False)

    def setLoading(self):
        self.state = self.STATE_LOADING
        self.iconView.setHidden_(True)
        self.spinner.setHidden_(False)
        self.spinner.startAnimation_(None)
        self.showFolderButton.setHidden_(True)
        self.showFolderButton.setEnabled_(False)

    def setSuccess(self):
        self.state = self.STATE_SUCCESS
        self.iconView.setHidden_(False)
        self.spinner.stopAnimation_(None)
        self.spinner.setHidden_(True)
        self.iconView.setImage_(
            create_symbol("checkmark.circle.fill")
        )
        self.iconView.setContentTintColor_(NSColor.systemGreenColor())
        self.showFolderButton.setHidden_(False)
        self.showFolderButton.setEnabled_(True)

    def setError(self):
        self.state = self.STATE_ERROR
        self.iconView.setHidden_(False)
        self.spinner.stopAnimation_(None)
        self.spinner.setHidden_(True)
        self.iconView.setImage_(
            create_symbol("xmark.circle.fill")
        )
        self.iconView.setContentTintColor_(NSColor.systemRedColor())
        self.showFolderButton.setHidden_(False)
        self.showFolderButton.setEnabled_(True)

    def showFolderButtonClicked_(self, sender):
        print(f"Show folder button clicked for item: {self.item_id}")


class PlaylistStatusView(NSView):

    def init(self):
        self = objc.super(PlaylistStatusView, self).init()
        if self is None:
            return None

        self.rows = {}
        self.itemOrder = []

        self.background = NSBox.alloc().init()
        self.background.setBoxType_(NSBoxCustom)
        self.background.setCornerRadius_(8.0)
        self.background.setBorderWidth_(1.0)
        self.background.setBorderColor_(NSColor.separatorColor())
        self.background.setFillColor_(NSColor.tertiarySystemFillColor())
        self.background.setContentViewMargins_(NSMakeSize(0.0, 0.0))

        self.progressIndicator = NSProgressIndicator.alloc().init()
        self.progressIndicator.setStyle_(NSProgressIndicatorStyleBar)
        self.progressIndicator.setIndeterminate_(False)
        self.progressIndicator.setMinValue_(0)
        self.progressIndicator.setMaxValue_(100)
        self.progressIndicator.setControlSize_(NSControlSizeLarge)

        self.progressLabel = NSTextField.labelWithString_("0%")
        self.progressLabel.setFont_(
            NSFont.systemFontOfSize_weight_(
                NSFont.systemFontSize(),
                NSFontWeightSemibold,
            )
        )
        self.progressLabel.setTextColor_(NSColor.secondaryLabelColor())

        self.headerStack = NSStackView.stackViewWithViews_([
            self.progressIndicator,
            self.progressLabel,
        ])
        self.headerStack.setBackgroundColor_(NSColor.clearColor())
        self.headerStack.setOrientation_(NSUserInterfaceLayoutOrientationHorizontal)
        self.headerStack.setAlignment_(NSLayoutAttributeCenterY)
        self.headerStack.setDistribution_(NSStackViewDistributionFill)
        self.headerStack.setSpacing_(8)

        self.headerEffectView = NSVisualEffectView.alloc().init()
        self.headerEffectView.setCornerRadius_(8.0)
        self.headerEffectView.setMaterial_(NSVisualEffectMaterialHeaderView)
        self.headerEffectView.setBlendingMode_(NSVisualEffectBlendingModeWithinWindow)
        self.headerEffectView.setState_(NSVisualEffectStateActive)
        self.headerEffectView.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.contentStack = NSStackView.alloc().init()
        self.contentStack.setOrientation_(NSUserInterfaceLayoutOrientationVertical)
        self.contentStack.setAlignment_(NSLayoutAttributeLeading)
        self.contentStack.setSpacing_(10)
        self.contentStack.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.scrollView = NSScrollView.alloc().init()
        self.scrollView.setHasVerticalScroller_(True)
        self.scrollView.setDrawsBackground_(False)
        self.scrollView.setAutomaticallyAdjustsContentInsets_(False)
        self.scrollView.setContentInsets_((HEADER_HEIGHT, 0, 0, 0))
        scrollContentView = self.scrollView.contentView()
        
        self.documentView = FlippedView.alloc().init()
        self.documentView.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.documentView.addSubview_(self.contentStack)
        self.scrollView.setDocumentView_(self.documentView)

        # self.separator = CurrentStepSeparator.alloc().init()
        self.headerEffectView.addSubview_(self.headerStack)
        # self.headerEffectView.addSubview_(self.separator)

        bgContent = self.background.contentView()
        bgContent.addSubview_(self.scrollView)
        bgContent.addSubview_positioned_relativeTo_(
            self.headerEffectView,
            NSWindowAbove,
            self.scrollView,
        )

        self.addSubview_(self.background)

        # self.separator.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.background.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.headerEffectView.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.headerStack.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.scrollView.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.contentStack.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([
            # self.separator.leadingAnchor().constraintEqualToAnchor_(self.headerEffectView.leadingAnchor()),
            # self.separator.trailingAnchor().constraintEqualToAnchor_(self.headerEffectView.trailingAnchor()),
            # self.separator.bottomAnchor().constraintEqualToAnchor_(self.headerEffectView.bottomAnchor()),
            # self.separator.heightAnchor().constraintEqualToConstant_(1),

            self.background.leadingAnchor().constraintEqualToAnchor_(self.leadingAnchor()),
            self.background.trailingAnchor().constraintEqualToAnchor_(self.trailingAnchor()),
            self.background.topAnchor().constraintEqualToAnchor_(self.topAnchor()),
            self.background.bottomAnchor().constraintEqualToAnchor_(self.bottomAnchor()),

            self.headerEffectView.leadingAnchor().constraintEqualToAnchor_(bgContent.leadingAnchor()),
            self.headerEffectView.trailingAnchor().constraintEqualToAnchor_(bgContent.trailingAnchor()),
            self.headerEffectView.topAnchor().constraintEqualToAnchor_(bgContent.topAnchor()),
            self.headerEffectView.heightAnchor().constraintEqualToConstant_(HEADER_HEIGHT),

            self.headerStack.leadingAnchor().constraintEqualToAnchor_constant_(self.headerEffectView.leadingAnchor(), 12),
            self.headerStack.trailingAnchor().constraintEqualToAnchor_constant_(self.headerEffectView.trailingAnchor(), -12),
            self.headerStack.centerYAnchor().constraintEqualToAnchor_(self.headerEffectView.centerYAnchor()),

            self.progressIndicator.heightAnchor().constraintEqualToConstant_(10),

            self.scrollView.leadingAnchor().constraintEqualToAnchor_(bgContent.leadingAnchor()),
            self.scrollView.trailingAnchor().constraintEqualToAnchor_(bgContent.trailingAnchor()),
            self.scrollView.topAnchor().constraintEqualToAnchor_(bgContent.topAnchor()),
            self.scrollView.bottomAnchor().constraintEqualToAnchor_(bgContent.bottomAnchor()),

            self.contentStack.leadingAnchor().constraintEqualToAnchor_(self.documentView.leadingAnchor()),
            self.contentStack.trailingAnchor().constraintEqualToAnchor_(self.documentView.trailingAnchor()),
            self.contentStack.topAnchor().constraintEqualToAnchor_(self.documentView.topAnchor()),
            self.contentStack.bottomAnchor().constraintEqualToAnchor_(self.documentView.bottomAnchor()),
            self.contentStack.widthAnchor().constraintEqualToAnchor_(scrollContentView.widthAnchor()),
        ])

        return self

    def _appendRowWithSeparator_(self, row):
        # if self.contentStack.arrangedSubviews():
        #     separator = CurrentStepSeparator.alloc().init()
        #     self.contentStack.addArrangedSubview_(separator)
        self.contentStack.addArrangedSubview_(row)
        separator = CurrentStepSeparator.alloc().init()
        self.contentStack.addArrangedSubview_(separator)

    def setItems_(self, items: list[PlaylistItemStatus]):
        self.reset()
        self.rows = {}
        self.itemOrder = []

        for item in items:
            item_id = item.id
            name = item.name
            action = item.action

            if item_id is None:
                continue

            row = PlaylistItemRowView.alloc().init()
            row.configureWithId_name_action_(item_id, name or "", action or "")
            row.setPending()

            self.rows[item_id] = row
            self.itemOrder.append(item_id)
            self._appendRowWithSeparator_(row)

        self.setProgressValue_(0)

    def startItem_(self, item_id):
        row = self.rows.get(item_id)
        if row is None:
            return
        row.setLoading()
        self._updateProgress()

    def updateItem_action_description_(self, item_id, action=None, description=None):
        row = self.rows.get(item_id)
        if row is None:
            return

        if action is not None:
            row.actionLabel.setStringValue_(action)

        if description is not None:
            row.setDescription_(description)

    def completeItemSuccess_description_(self, item_id, description=None):
        row = self.rows.get(item_id)
        if row is None:
            return

        row.setSuccess()
        if description is not None:
            row.setDescription_(description)
        self._updateProgress()

    def completeItemError_description_(self, item_id, description=None):
        row = self.rows.get(item_id)
        if row is None:
            return

        row.setError()
        if description is not None:
            row.setDescription_(description)
        self._updateProgress()

    def setProgressValue_(self, percent):
        percent_value = max(0, min(100, percent))
        self.progressLabel.setStringValue_(f"{int(percent_value)}%")

        def animation(context):
            context.setDuration_(0.25)
            self.progressIndicator.animator().setDoubleValue_(percent_value)

        NSAnimationContext.runAnimationGroup_completionHandler_(animation, None)

    def _updateProgress(self):
        total = len(self.rows)
        if total == 0:
            self.setProgressValue_(0)
            return

        completed = 0
        for row in self.rows.values():
            if row.state in (PlaylistItemRowView.STATE_SUCCESS, PlaylistItemRowView.STATE_ERROR):
                completed += 1

        self.setProgressValue_(completed / total * 100)

    def reset(self):
        for view in list(self.contentStack.arrangedSubviews()):
            self.contentStack.removeArrangedSubview_(view)
            view.removeFromSuperview()

        self.rows = {}
        self.itemOrder = []
        self.setProgressValue_(0)
