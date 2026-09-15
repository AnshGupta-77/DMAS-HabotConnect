from django.urls import reverse
from rest_framework import status

from documents.models import ActivityLog, Document

from .helpers import auth_client
from .test_workflow import WorkflowTestBase


class ChangesRequestedEditTests(WorkflowTestBase):
    def setUp(self):
        super().setUp()
        self.submit()
        self.review()
        self.client.post(
            reverse("document-request-changes", args=[self.doc_id]), {"comment": "Fix section 2."}, format="json"
        )

    def test_patch_returns_document_to_draft_and_allows_resubmission(self):
        auth_client(self.client, self.creator)
        resp = self.client.patch(
            reverse("document-detail", args=[self.doc_id]), {"title": "Policy v2"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], Document.Status.DRAFT)
        self.assertEqual(self.submit().status_code, status.HTTP_200_OK)


class MalformedInputTests(WorkflowTestBase):
    def test_non_numeric_version_id_returns_404(self):
        resp = self.client.get(f"/api/documents/{self.doc_id}/versions/abc/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_numeric_version_download_id_returns_404(self):
        resp = self.client.get(f"/api/documents/{self.doc_id}/versions/abc/download/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_string_reject_reason_returns_400(self):
        self.submit()
        self.review()
        resp = self.client.post(reverse("document-reject", args=[self.doc_id]), {"reason": 123}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Document.objects.get(id=self.doc_id).status, Document.Status.UNDER_REVIEW)

    def test_non_string_change_request_comment_returns_400(self):
        self.submit()
        self.review()
        resp = self.client.post(
            reverse("document-request-changes", args=[self.doc_id]), {"comment": ["x"]}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteConsistencyTests(WorkflowTestBase):
    def test_delete_removes_files_after_commit_and_logs_activity(self):
        document = Document.objects.get(id=self.doc_id)
        storage, name = document.file.storage, document.file.name
        auth_client(self.client, self.creator)
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.delete(reverse("document-detail", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(storage.exists(name))
        self.assertTrue(ActivityLog.objects.filter(action=ActivityLog.Action.DELETED, document=None).exists())
