from .models import ActivityLog


def log_activity(*, document, user, action, description=""):
    return ActivityLog.objects.create(
        document=document, user=user, action=action, description=description
    )
