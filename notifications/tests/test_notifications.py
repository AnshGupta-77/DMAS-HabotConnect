from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.tests.helpers import auth_client, make_user
from notifications.models import Notification
from notifications.services import notify


class NotificationTests(APITestCase):
    def setUp(self):
        self.alice = make_user("alice", "creator")
        self.bob = make_user("bob", "creator")
        notify([self.alice], "You have a document waiting for review.")
        notify([self.alice], "Your document has been approved.")
        notify([self.bob], "Changes have been requested for your document.")

    def test_requires_auth(self):
        resp = self.client.get(reverse("notification-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_lists_only_own_notifications_newest_first(self):
        auth_client(self.client, self.alice)
        resp = self.client.get(reverse("notification-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)
        self.assertEqual(resp.data["results"][0]["message"], "Your document has been approved.")

    def test_mark_own_notification_read(self):
        note = Notification.objects.filter(user=self.alice).first()
        auth_client(self.client, self.alice)
        resp = self.client.patch(reverse("notification-read", args=[note.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertTrue(note.is_read)

    def test_cannot_mark_other_users_notification_read_idor(self):
        note = Notification.objects.filter(user=self.bob).first()
        auth_client(self.client, self.alice)
        resp = self.client.patch(reverse("notification-read", args=[note.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
