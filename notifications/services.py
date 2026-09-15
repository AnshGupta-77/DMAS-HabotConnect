from .models import Notification


def notify(users, message):
    Notification.objects.bulk_create(Notification(user=user, message=message) for user in users)
