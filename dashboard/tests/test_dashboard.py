from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document
from documents.tests.helpers import auth_client, make_category, make_user, pdf_file


class DashboardTests(APITestCase):
    def setUp(self):
        self.creator = make_user("creator1", "creator")
        self.other_creator = make_user("creator2", "creator")
        self.reviewer = make_user("reviewer1", "reviewer")
        self.admin = make_user("admin1", "admin")
        self.category = make_category()

        auth_client(self.client, self.creator)
        for i in range(3):
            self.client.post(
                reverse("document-list"),
                {"title": f"Doc {i}", "category": self.category.id, "file": pdf_file()},
                format="multipart",
            )
        docs = list(Document.objects.filter(created_by=self.creator))
        docs[0].status = Document.Status.SUBMITTED
        docs[0].save()
        docs[1].status = Document.Status.UNDER_REVIEW
        docs[1].save()

        auth_client(self.client, self.other_creator)
        self.client.post(
            reverse("document-list"),
            {"title": "Other doc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        other_doc = Document.objects.get(title="Other doc")
        other_doc.status = Document.Status.APPROVED
        other_doc.save()

    def test_requires_auth(self):
        self.client.credentials()
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_sees_all(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_documents"], 4)
        self.assertEqual(resp.data["submitted_documents"], 1)
        self.assertEqual(resp.data["pending_reviews"], 1)
        self.assertEqual(resp.data["approved_documents"], 1)
        self.assertEqual(resp.data["draft_documents"], 1)

    def test_creator_sees_own_only(self):
        auth_client(self.client, self.creator)
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.data["total_documents"], 3)

    def test_reviewer_excludes_drafts(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.data["total_documents"], 3)
        self.assertEqual(resp.data["draft_documents"], 0)

    def test_dashboard_query_count(self):
        auth_client(self.client, self.admin)
        with self.assertNumQueries(2):
            self.client.get(reverse("dashboard"))
