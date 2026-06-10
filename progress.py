from dataclasses import dataclass

import objc

from AppKit import (
    NSAnimationContext,
    NSLayoutAttributeCenterY,
    NSLayoutConstraint,
    NSBox,
    NSBoxSeparator,
    NSColor,
    NSControlSizeSmall,
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
    NSProgressIndicatorStyleSpinning,
    NSTextField,
    NSStackView,
    NSStackViewDistributionFill,
    NSStackViewGravityCenter,
    NSStackViewGravityLeading,
    NSUserInterfaceLayoutOrientationHorizontal,
    NSUserInterfaceLayoutOrientationVertical,
    NSView,
    NSBoxCustom
)


# ============================================================
# Model
# ============================================================

@dataclass
class ProgressStep:
    title: str
    description: str | None = None
    icon: str | None = None
    loading: bool = False
    success: bool | None = None


# ============================================================
# Helpers
# ============================================================

def create_symbol(name: str, point_size: float = 14.0):
    conf = NSImageSymbolConfiguration.configurationWithPointSize_weight_(
        point_size,
        NSFontWeightMedium,
    )

    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
        name,
        None,
    )

    return image.imageWithSymbolConfiguration_(conf)


# ============================================================
# Separator
# ============================================================

class CurrentStepSeparator(NSView):

    def init(self):
        self = objc.super(CurrentStepSeparator, self).init()
        if self is None:
            return None

        line = NSBox.alloc().initWithFrame_(NSMakeRect(0, 0, 0, 1))
        line.setBoxType_(NSBoxCustom)
        line.setBorderWidth_(0.0)
        line.setFillColor_(NSColor.separatorColor())
        line.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.addSubview_(line)

        NSLayoutConstraint.activateConstraints_([
            line.leadingAnchor().constraintEqualToAnchor_(
                self.leadingAnchor()
            ),
            line.trailingAnchor().constraintEqualToAnchor_(
                self.trailingAnchor()
            ),
            line.centerYAnchor().constraintEqualToAnchor_(
                self.centerYAnchor()
            ),
            line.heightAnchor().constraintEqualToConstant_(1),
        ])

        return self


# ============================================================
# Row
# ============================================================

class StepRowView(NSView):

    def init(self):
        self = objc.super(StepRowView, self).init()
        if self is None:
            return None

        self.iconView = NSImageView.alloc().init()

        self.spinner = NSProgressIndicator.alloc().init()
        self.spinner.setStyle_(NSProgressIndicatorStyleSpinning)
        self.spinner.setControlSize_(NSControlSizeSmall)
        self.spinner.setDisplayedWhenStopped_(False)

        self.titleLabel = NSTextField.labelWithString_("")
        self.titleLabel.setFont_(
            NSFont.systemFontOfSize_weight_(
                13,
                NSFontWeightSemibold,
            )
        )
        self.titleLabel.setAlignment_(NSLeftTextAlignment)

        self.descriptionLabel = NSTextField.labelWithString_("")
        self.descriptionLabel.setFont_(
            NSFont.systemFontOfSize_(11)
        )
        self.descriptionLabel.setTextColor_(
            NSColor.secondaryLabelColor()
        )
        self.descriptionLabel.setAlignment_(NSLeftTextAlignment)

        self.textStack = NSStackView.stackViewWithViews_([
            self.titleLabel,
            self.descriptionLabel,
        ])

        self.textStack.setOrientation_(
            NSUserInterfaceLayoutOrientationVertical
        )

        self.textStack.setAlignment_(NSStackViewGravityLeading)
        self.textStack.setDistribution_(NSStackViewDistributionFill)
        self.textStack.setSpacing_(2)

        self.leadingContainer = NSView.alloc().init()
        self.leadingContainer.setTranslatesAutoresizingMaskIntoConstraints_(False)

        self.leadingContainer.addSubview_(self.iconView)
        self.leadingContainer.addSubview_(self.spinner)

        self.addSubview_(self.leadingContainer)
        self.addSubview_(self.textStack)

        for view in (
            self.leadingContainer,
            self.textStack,
            self.iconView,
            self.spinner,
        ):
            view.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([

            self.leadingContainer.leadingAnchor().constraintEqualToAnchor_(
                self.leadingAnchor()
            ),
            self.leadingContainer.centerYAnchor().constraintEqualToAnchor_(
                self.centerYAnchor()
            ),
            self.leadingContainer.widthAnchor().constraintEqualToConstant_(18),
            self.leadingContainer.heightAnchor().constraintEqualToConstant_(18),

            self.iconView.centerXAnchor().constraintEqualToAnchor_(
                self.leadingContainer.centerXAnchor()
            ),
            self.iconView.centerYAnchor().constraintEqualToAnchor_(
                self.leadingContainer.centerYAnchor()
            ),

            self.spinner.centerXAnchor().constraintEqualToAnchor_(
                self.leadingContainer.centerXAnchor()
            ),
            self.spinner.centerYAnchor().constraintEqualToAnchor_(
                self.leadingContainer.centerYAnchor()
            ),

            self.textStack.leadingAnchor().constraintEqualToAnchor_constant_(
                self.leadingContainer.trailingAnchor(),
                10,
            ),
            self.textStack.trailingAnchor().constraintEqualToAnchor_(
                self.trailingAnchor()
            ),
            self.textStack.topAnchor().constraintEqualToAnchor_(
                self.topAnchor()
            ),
            self.textStack.bottomAnchor().constraintEqualToAnchor_(
                self.bottomAnchor()
            ),
        ])

        self.iconView.setHidden_(True)
        self.spinner.setHidden_(True)
        self.descriptionLabel.setHidden_(True)

        return self

    def setTitle_description_(self, title, description):

        self.titleLabel.setStringValue_(title)

        if description:
            self.descriptionLabel.setStringValue_(description)
            self.descriptionLabel.setHidden_(False)
        else:
            self.descriptionLabel.setStringValue_("")
            self.descriptionLabel.setHidden_(True)

    def setIcon_(self, symbol_name):

        self.spinner.stopAnimation_(None)
        self.spinner.setHidden_(True)

        self.iconView.setHidden_(False)
        self.iconView.setImage_(
            create_symbol(symbol_name)
        )

        self.iconView.setContentTintColor_(
            NSColor.secondaryLabelColor()
        )

    def setLoading(self):

        self.iconView.setHidden_(True)

        self.spinner.setHidden_(False)
        self.spinner.startAnimation_(None)

    def setSuccess(self):

        self.spinner.stopAnimation_(None)
        self.spinner.setHidden_(True)

        self.iconView.setHidden_(False)

        self.iconView.setImage_(
            create_symbol("checkmark.circle.fill")
        )

        self.iconView.setContentTintColor_(
            NSColor.systemGreenColor()
        )

    def setError(self):

        self.spinner.stopAnimation_(None)
        self.spinner.setHidden_(True)

        self.iconView.setHidden_(False)

        self.iconView.setImage_(
            create_symbol("xmark.circle.fill")
        )

        self.iconView.setContentTintColor_(
            NSColor.systemRedColor()
        )


# ============================================================
# Main View
# ============================================================

class ProgressStepsView(NSView):

    def init(self):
        self = objc.super(ProgressStepsView, self).init()
        if self is None:
            return None

        self.currentRow = None

        self.background = NSBox.alloc().init()
        self.background.setBoxType_(NSBoxCustom)
        self.background.setCornerRadius_(8.0)
        self.background.setBorderWidth_(1.0)
        self.background.setBorderColor_(NSColor.separatorColor())
        self.background.setFillColor_(NSColor.quaternarySystemFillColor())
        self.background.setContentViewMargins_(NSMakeSize(0.0, 0.0))

        self.stack = NSStackView.alloc().init()

        self.stack.setOrientation_(
            NSUserInterfaceLayoutOrientationVertical
        )

        self.stack.setAlignment_(NSStackViewGravityLeading)
        self.stack.setSpacing_(10)

        bgContent = self.background.contentView()
        bgContent.addSubview_(self.stack)
        self.addSubview_(self.background)

        self.background.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.stack.setTranslatesAutoresizingMaskIntoConstraints_(False)

        NSLayoutConstraint.activateConstraints_([

            self.background.leadingAnchor().constraintEqualToAnchor_(
                self.leadingAnchor()
            ),
            self.background.trailingAnchor().constraintEqualToAnchor_(
                self.trailingAnchor()
            ),
            self.background.topAnchor().constraintEqualToAnchor_(
                self.topAnchor()
            ),
            self.background.bottomAnchor().constraintEqualToAnchor_(
                self.bottomAnchor()
            ),

            self.stack.leadingAnchor().constraintEqualToAnchor_constant_(
                bgContent.leadingAnchor(),
                16,
            ),
            self.stack.trailingAnchor().constraintEqualToAnchor_constant_(
                bgContent.trailingAnchor(),
                -16,
            ),
            self.stack.topAnchor().constraintEqualToAnchor_constant_(
                bgContent.topAnchor(),
                16,
            ),
            self.stack.bottomAnchor().constraintEqualToAnchor_constant_(
                bgContent.bottomAnchor(),
                -16,
            ),
        ])

        return self

    # --------------------------------------------------------

    def _appendRowWithSeparator_(self, row):

        if self.stack.arrangedSubviews():
            separator = CurrentStepSeparator.alloc().init()
            self.stack.addArrangedSubview_(separator)

        self.stack.addArrangedSubview_(row)

    # --------------------------------------------------------

    def addStep_description_icon_(
        self,
        title,
        description=None,
        icon=None,
    ):
        row = StepRowView.alloc().init()

        row.setTitle_description_(
            title,
            description,
        )

        if icon:
            row.setIcon_(icon)

        self._appendRowWithSeparator_(row)

        self._animateInsertion_(row)

    # --------------------------------------------------------

    def beginCurrentStep_description_icon_(
        self,
        title,
        description=None,
        icon=None,
    ):
        # if self.currentRow:
        #     return

        self.currentRow = StepRowView.alloc().init()

        self.currentRow.setTitle_description_(
            title,
            description,
        )

        if icon:
            self.currentRow.setIcon_(icon)

        self.currentRow.setLoading()

        self._appendRowWithSeparator_(self.currentRow)

        self._animateInsertion_(self.currentRow)

    # --------------------------------------------------------

    def updateCurrentStep_description_(
        self,
        title=None,
        description=None,
    ):

        if not self.currentRow:
            return

        if title is not None:
            self.currentRow.titleLabel.setStringValue_(title)

        if description is not None:
            self.currentRow.setTitle_description_(
                self.currentRow.titleLabel.stringValue(),
                description,
            )

    # --------------------------------------------------------

    def finishCurrentStepSuccess_description_(
        self,
        title,
        description=None,
    ):

        if not self.currentRow:
            return

        self.currentRow.setTitle_description_(
            title,
            description,
        )

        self.currentRow.setSuccess()

        self.currentRow = None

    # --------------------------------------------------------

    def finishCurrentStepError_description_(
        self,
        title,
        description=None,
    ):
        if not self.currentRow:
            return

        self.currentRow.setTitle_description_(
            title,
            description,
        )

        self.currentRow.setError()

        self.currentRow = None

    # --------------------------------------------------------

    def reset(self):

        for view in list(self.stack.arrangedSubviews()):
            self.stack.removeArrangedSubview_(view)
            view.removeFromSuperview()

        self.currentRow = None

    # --------------------------------------------------------

    def _animateInsertion_(self, row):

        row.setAlphaValue_(0.0)

        targetHeight = row.fittingSize().height
        heightConstraint = row.heightAnchor().constraintEqualToConstant_(0)
        heightConstraint.setActive_(True)

        self.layoutSubtreeIfNeeded()

        def animation(context):
            context.setDuration_(0.20)
            row.animator().setAlphaValue_(1.0)
            heightConstraint.animator().setConstant_(targetHeight)
            self.animator().layoutSubtreeIfNeeded()

        def completion():
            heightConstraint.setActive_(False)

        NSAnimationContext.runAnimationGroup_completionHandler_(
            animation,
            completion,
        )