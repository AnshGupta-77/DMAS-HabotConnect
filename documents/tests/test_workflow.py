from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import ActivityLog, Document
from notifications.models import Notification

from .helpers import auth_client, make_category, make_user, pdf_file


class WorkflowTestBase(APITestCase):
    def setUp(self):
        self.creator = make_user("creator1", "creator")
        self.other_creator = make_user("creator2", "creator")
        self.reviewer = make_user("reviewer1", "reviewer")
        self.admin = make_user("admin1", "admin")
        self.category = make_category()
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Policy", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        self.doc_id = resp.data["id"]

    def submit(self, user=None):
        auth_client(self.client, user or self.creator)
        return self.client.post(reverse("document-submit", args=[self.doc_id]))

    def review(self, user=None):
        auth_client(self.client, user or self.reviewer)
        return self.client.post(reverse("document-review", args=[self.doc_id]))


class SubmitTests(WorkflowTestBase):
    def test_owner_can_submit(self):
        resp = self.submit()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=self.doc_id).status, Document.Status.SUBMITTED)
        self.assertTrue(
            Notification.objects.filter(user=self.reviewer, message__icontains="waiting for review").exists()
        )

    def test_other_creator_cannot_submit(self):
        resp = self.submit(self.other_creator)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_reviewer_cannot_submit(self):
        # reviewer can't see draft docs at all -> 404, still proves it can't act
        resp = self.submit(self.reviewer)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_double_submit_rejected(self):
        self.submit()
        resp = self.submit()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewTests(WorkflowTestBase):
    def setUp(self):
        super().setUp()
        self.submit()

    def test_reviewer_can_review(self):
        resp = self.review()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=self.doc_id).status, Document.Status.UNDER_REVIEW)

    def test_creator_cannot_review(self):
        resp = self.review(self.creator)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_review_draft_document_fails(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Draft doc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        draft_id = resp.data["id"]
        auth_client(self.client, self.reviewer)
        resp = self.client.post(reverse("document-review", args=[draft_id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class ApproveRejectTests(WorkflowTestBase):
    def setUp(self):
        super().setUp()
        self.submit()
        self.review()

    def test_reviewer_can_approve(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(reverse("document-approve", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=self.doc_id).status, Document.Status.APPROVED)
        self.assertTrue(
            Notification.objects.filter(user=self.creator, message__icontains="approved").exists()
        )
        self.assertTrue(
            ActivityLog.objects.filter(document_id=self.doc_id, action=ActivityLog.Action.APPROVED).exists()
        )

    def test_creator_cannot_approve_own_document(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(reverse("document-approve", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_draft_cannot_approve(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(
            reverse("document-list"),
            {"title": "Draft doc", "category": self.category.id, "file": pdf_file()},
            format="multipart",
        )
        draft_id = resp.data["id"]
        auth_client(self.client, self.admin)
        resp = self.client.post(reverse("document-approve", args=[draft_id]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approved_cannot_approve_again(self):
        auth_client(self.client, self.reviewer)
        self.client.post(reverse("document-approve", args=[self.doc_id]))
        resp = self.client.post(reverse("document-approve", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_requires_reason(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(reverse("document-reject", args=[self.doc_id]), {"reason": ""})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_whitespace_reason_rejected(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(reverse("document-reject", args=[self.doc_id]), {"reason": "   "})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_with_reason_ok(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(
            reverse("document-reject", args=[self.doc_id]), {"reason": "Please update the budget section."}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=self.doc_id).status, Document.Status.REJECTED)
        self.assertTrue(
            Notification.objects.filter(user=self.creator, message__icontains="rejected").exists()
        )

    def test_rejected_cannot_approve_without_resubmission(self):
        auth_client(self.client, self.reviewer)
        self.client.post(reverse("document-reject", args=[self.doc_id]), {"reason": "No good."})
        resp = self.client.post(reverse("document-approve", args=[self.doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creator_cannot_reject(self):
        auth_client(self.client, self.creator)
        resp = self.client.post(reverse("document-reject", args=[self.doc_id]), {"reason": "no"})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class RequestChangesTests(WorkflowTestBase):
    def setUp(self):
        super().setUp()
        self.submit()
        self.review()

    def test_request_changes_requires_comment(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(reverse("document-request-changes", args=[self.doc_id]), {"comment": ""})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_request_changes_ok(self):
        auth_client(self.client, self.reviewer)
        resp = self.client.post(
            reverse("document-request-changes", args=[self.doc_id]),
            {"comment": "Please update the description."},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        doc = Document.objects.get(id=self.doc_id)
        self.assertEqual(doc.status, Document.Status.CHANGES_REQUESTED)
        self.assertTrue(doc.comments.filter(comment="Please update the description.").exists())
        self.assertTrue(
            Notification.objects.filter(user=self.creator, message__icontains="Changes").exists()
        )
