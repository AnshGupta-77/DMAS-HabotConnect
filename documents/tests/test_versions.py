from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import ActivityLog, Document

from .helpers import auth_client, make_category, make_user, pdf_file


class VersionTests(APITestCase):
    def setUp(self):
        self.creator = make_user("creator1", "creator")
        self.other_creator = make_user("creator2", "creator")
        self.admin = make_user("admin1", "admin")
        self.reviewer = make_user("reviewer1", "reviewer")
        self.category = make_category()
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.doc_id = resp.data["id"]

    def test_version_number_increments(self):
        resp = self.client.post(
            reverse("document-versions", args=[self.doc_id]),
            {"file": pdf_file(name="v2.pdf"), "comment": "Updated content"},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["version_number"], 2)
        doc = Document.objects.get(id=self.doc_id)
        self.assertEqual(doc.current_version, 2)
        self.assertEqual(doc.status, Document.Status.DRAFT)
        self.assertTrue(
            ActivityLog.objects.filter(
                document_id=self.doc_id, action=ActivityLog.Action.VERSION_CREATED
            ).exists()
        )

    def test_new_version_on_approved_document_keeps_old_file_record(self):
        doc = Document.objects.get(id=self.doc_id)
        doc.status = Document.Status.APPROVED
        doc.save()

        resp = self.client.post(
            reverse("document-versions", args=[self.doc_id]),
            {"file": pdf_file(name="v2.pdf")},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        doc.refresh_from_db()
        self.assertEqual(doc.status, Document.Status.DRAFT)
        self.assertEqual(doc.versions.count(), 2)
        self.assertTrue(doc.versions.filter(version_number=1).exists())

    def test_blocked_while_under_review(self):
        doc = Document.objects.get(id=self.doc_id)
        doc.status = Document.Status.UNDER_REVIEW
        doc.save()
        resp = self.client.post(
            reverse("document-versions", args=[self.doc_id]),
            {"file": pdf_file(name="v2.pdf")},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owner_forbidden(self):
        auth_client(self.client, self.other_creator)
        resp = self.client.post(
            reverse("document-versions", args=[self.doc_id]),
            {"file": pdf_file(name="v2.pdf")},
            format="multipart",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_version_from_other_document_404(self):
        auth_client(self.client, self.other_creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Other doc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        other_doc_id = resp.data["id"]
        v1 = Document.objects.get(id=other_doc_id).versions.first()

        auth_client(self.client, self.creator)
        resp = self.client.get(reverse("document-version-detail", args=[self.doc_id, v1.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_file_rejected(self):
        bad = pdf_file(name="virus.exe", content=b"MZ\x90\x00")
        resp = self.client.post(
            reverse("document-versions", args=[self.doc_id]), {"file": bad}, format="multipart"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_and_retrieve_versions(self):
        list_resp = self.client.get(reverse("document-versions", args=[self.doc_id]))
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        v1_id = list_resp.data["results"][0]["id"]
        detail_resp = self.client.get(reverse("document-version-detail", args=[self.doc_id, v1_id]))
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)

    def test_version_download(self):
        list_resp = self.client.get(reverse("document-versions", args=[self.doc_id]))
        v1_id = list_resp.data["results"][0]["id"]
        resp = self.client.get(reverse("document-version-download", args=[self.doc_id, v1_id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
