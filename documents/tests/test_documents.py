from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import ActivityLog, Document

from .helpers import auth_client, make_category, make_user, pdf_file


class DocumentCreateTests(APITestCase):
    def setUp(self):
        self.creator = make_user("creator1", "creator")
        self.reviewer = make_user("reviewer1", "reviewer")
        self.category = make_category()

    def test_creator_can_create_document(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "description": "desc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(title="Policy")
        self.assertEqual(doc.status, Document.Status.DRAFT)
        self.assertEqual(doc.current_version, 1)
        self.assertEqual(doc.versions.count(), 1)
        self.assertTrue(
            ActivityLog.objects.filter(document=doc, action=ActivityLog.Action.CREATED).exists()
        )

    def test_reviewer_cannot_upload(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "description": "desc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_title_rejected(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"description": "desc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_category_rejected(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "file": pdf_file()},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_file_rejected(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_extension_rejected(self):
        auth_client(self.client, self.creator)
        bad = pdf_file(name="virus.exe", content=b"MZ\x90\x00")
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": bad},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_spoofed_extension_rejected(self):
        auth_client(self.client, self.creator)
        spoofed = pdf_file(name="virus.pdf", content=b"MZ\x90\x00fakecontent")
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": spoofed},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oversized_file_rejected(self):
        auth_client(self.client, self.creator)
        big = pdf_file(content=b"%PDF-1.4\n" + b"0" * (11 * 1024 * 1024))
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": big},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_rejected(self):
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentRetrieveDeleteTests(APITestCase):
    def setUp(self):
        self.creator = make_user("creator1", "creator")
        self.other_creator = make_user("creator2", "creator")
        self.admin = make_user("admin1", "admin")
        self.category = make_category()
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.doc_id = resp.data["id"]

    def test_other_creator_cannot_retrieve(self):
        auth_client(self.client, self.other_creator)
        resp = self.client.get(reverse("document-detail", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_retrieve(self):
        auth_client(self.client, self.creator)
        resp = self.client.get(reverse("document-detail", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_status_field_ignored_on_patch(self):
        auth_client(self.client, self.creator)
        resp = self.client.patch(
            reverse("document-detail", args=[self.doc_id]), {"status": "approved"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=self.doc_id).status, Document.Status.DRAFT)

    def test_delete_own_draft_ok(self):
        auth_client(self.client, self.creator)
        resp = self.client.delete(reverse("document-detail", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=self.doc_id).exists())
        self.assertTrue(ActivityLog.objects.filter(action=ActivityLog.Action.DELETED).exists())

    def test_admin_can_delete_any(self):
        auth_client(self.client, self.admin)
        resp = self.client.delete(reverse("document-detail", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_draft_delete_blocked_for_creator(self):
        doc = Document.objects.get(id=self.doc_id)
        doc.status = Document.Status.SUBMITTED
        doc.save()
        auth_client(self.client, self.creator)
        resp = self.client.delete(reverse("document-detail", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_edit_approved_blocked(self):
        doc = Document.objects.get(id=self.doc_id)
        doc.status = Document.Status.APPROVED
        doc.save()
        auth_client(self.client, self.creator)
        resp = self.client.patch(
            reverse("document-detail", args=[self.doc_id]), {"title": "New"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_download_requires_access(self):
        auth_client(self.client, self.other_creator)
        resp = self.client.get(reverse("document-download", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_ok_for_owner(self):
        auth_client(self.client, self.creator)
        resp = self.client.get(reverse("document-download", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
