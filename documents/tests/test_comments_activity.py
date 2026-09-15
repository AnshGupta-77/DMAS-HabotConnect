from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import ActivityLog

from .helpers import auth_client, make_category, make_user, pdf_file


class CommentsActivityTests(APITestCase):
    def setUp(self):
        self.creator = make_user("creator1", "creator")
        self.other_creator = make_user("creator2", "creator")
        self.reviewer = make_user("reviewer1", "reviewer")
        self.category = make_category()
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.doc_id = resp.data["id"]

    def test_add_comment_ok(self):
        resp = self.client.post(reverse("document-comments", args=[self.doc_id]), {"comment": "Looks good"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["username"], "creator1")

    def test_empty_comment_rejected(self):
        resp = self.client.post(reverse("document-comments", args=[self.doc_id]), {"comment": ""})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_whitespace_comment_rejected(self):
        resp = self.client.post(reverse("document-comments", args=[self.doc_id]), {"comment": "   "})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_on_inaccessible_document_404(self):
        auth_client(self.client, self.other_creator)
        resp = self.client.post(reverse("document-comments", args=[self.doc_id]), {"comment": "hi"})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_user_cannot_be_impersonated(self):
        resp = self.client.post(
            reverse("document-comments", args=[self.doc_id]), {"comment": "hi", "user": 999}
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["user"], self.creator.id)

    def test_list_comments(self):
        self.client.post(reverse("document-comments", args=[self.doc_id]), {"comment": "First"})
        resp = self.client.get(reverse("document-comments", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_activity_log_created_and_ordered(self):
        resp = self.client.get(reverse("document-activity", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["results"][0]["action"], ActivityLog.Action.CREATED)

    def test_activity_on_inaccessible_document_404(self):
        auth_client(self.client, self.other_creator)
        resp = self.client.get(reverse("document-activity", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
