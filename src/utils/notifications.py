import uuid
from UserNotifications import (
    UNMutableNotificationContent,
    UNTimeIntervalNotificationTrigger,
    UNNotificationRequest,
    UNUserNotificationCenter,
    UNNotificationSound,
)

def send_notification(title: str, subtitle: str = "", body: str = ""):
    content = UNMutableNotificationContent.alloc().init()
    content.setTitle_(title)
    if subtitle:
        content.setSubtitle_(subtitle)
    content.setBody_(body)
    content.setSound_(UNNotificationSound.defaultSound())

    # “Now”: schedule for 1 second later (required by UN*)
    trigger = UNTimeIntervalNotificationTrigger.triggerWithTimeInterval_repeats_(1, False)

    request = UNNotificationRequest.requestWithIdentifier_content_trigger_(
        str(uuid.uuid4()), content, trigger
    )

    def _added(error):
        if error:
            print("Failed to schedule notification:", error)

    UNUserNotificationCenter.currentNotificationCenter().addNotificationRequest_withCompletionHandler_(request, _added)
