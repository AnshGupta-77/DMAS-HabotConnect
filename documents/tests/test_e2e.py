from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import ActivityLog, Document
from notifications.models import Notification

from .helpers import pdf_file


class EndToEndFlowTests(APITestCase):
    """Replicates the 13-step flow in Product-Brief.md §26 / rules.md §40."""

    def test_full_flow_success_path(self):
        # 1. User registers (creator)
        reg = self.client.post(
            reverse("register"),
            {"username": "carla", "email": "carla@example.com", "password": "StrongPass123", "role": "creator"},
        )
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)

        # register reviewer too
        self.client.post(
            reverse("register"),
            {"username": "rick", "email": "rick@example.com", "password": "StrongPass123", "role": "reviewer"},
        )

        # 2. User logs in
        login = self.client.post(reverse("login"), {"username": "carla", "password": "StrongPass123"})
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        access = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        from documents.models import Category

        category = Category.objects.first()

        # 3 & 4. Creator uploads document, saved as Draft
        create = self.client.post(
            reverse("document-list"),
            {"title": "Project Proposal", "description": "v1", "category": category.id, "file": pdf_file()},
            format="multipart",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        doc_id = create.data["id"]
        self.assertEqual(Document.objects.get(id=doc_id).status, Document.Status.DRAFT)

        # 5. Creator submits document
        submit = self.client.post(reverse("document-submit", args=[doc_id]))
        self.assertEqual(submit.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=doc_id).status, Document.Status.SUBMITTED)

        reviewer_login = self.client.post(reverse("login"), {"username": "rick", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {reviewer_login.data['access']}")

        # 6. Reviewer sees submitted document
        listing = self.client.get(reverse("document-list"))
        self.assertIn(doc_id, [d["id"] for d in listing.data["results"]])

        # 7. Reviewer reviews document
        review = self.client.post(reverse("document-review", args=[doc_id]))
        self.assertEqual(review.status_code, status.HTTP_200_OK)

        # 8. Reviewer adds comment
        comment = self.client.post(
            reverse("document-comments", args=[doc_id]), {"comment": "Please update the budget section."}
        )
        self.assertEqual(comment.status_code, status.HTTP_201_CREATED)

        # 9. Reviewer approves
        approve = self.client.post(reverse("document-approve", args=[doc_id]))
        self.assertEqual(approve.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.get(id=doc_id).status, Document.Status.APPROVED)

        # 10. Creator receives notification
        self.assertTrue(
            Notification.objects.filter(user__username="carla", message__icontains="approved").exists()
        )

        # 11. Approved document can be viewed
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        view = self.client.get(reverse("document-detail", args=[doc_id]))
        self.assertEqual(view.status_code, status.HTTP_200_OK)
        self.assertEqual(view.data["status"], "approved")

        # 12. Creator creates a new version
        new_version = self.client.post(
            reverse("document-versions", args=[doc_id]), {"file": pdf_file(name="v2.pdf")}, format="multipart"
        )
        self.assertEqual(new_version.status_code, status.HTTP_201_CREATED)
        self.assertEqual(new_version.data["version_number"], 2)
        self.assertEqual(Document.objects.get(id=doc_id).status, Document.Status.DRAFT)

        # 13. Activity is recorded
        activity = self.client.get(reverse("document-activity", args=[doc_id]))
        actions = {entry["action"] for entry in activity.data["results"]}
        self.assertIn(ActivityLog.Action.CREATED, actions)
        self.assertIn(ActivityLog.Action.SUBMITTED, actions)
        self.assertIn(ActivityLog.Action.REVIEWED, actions)
        self.assertIn(ActivityLog.Action.APPROVED, actions)
        self.assertIn(ActivityLog.Action.VERSION_CREATED, actions)

    def test_unauthorized_branches(self):
        creator = self.client.post(
            reverse("register"),
            {"username": "greg", "email": "greg@example.com", "password": "StrongPass123", "role": "creator"},
        )
        self.assertEqual(creator.status_code, status.HTTP_201_CREATED)

        # unauthenticated access to protected endpoint
        resp = self.client.get(reverse("document-list"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        login = self.client.post(reverse("login"), {"username": "greg", "password": "StrongPass123"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        from documents.models import Category

        category = Category.objects.first()
        create = self.client.post(
            reverse("document-list"),
            {"title": "Doc", "category": category.id, "file": pdf_file()},
            format="multipart",
        )
        doc_id = create.data["id"]

        # creator cannot approve their own document (wrong role, draft status too)
        resp = self.client.post(reverse("document-approve", args=[doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # creator cannot review (wrong role)
        resp = self.client.post(reverse("document-review", args=[doc_id]))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
