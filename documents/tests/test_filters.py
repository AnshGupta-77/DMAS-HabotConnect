from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .helpers import auth_client, make_category, make_user, pdf_file


class DocumentFilterTests(APITestCase):
    def setUp(self):
        self.admin = make_user("admin1", "admin")
        self.hr = make_category("HR")
        self.finance = make_category("Finance")
        self.creator = make_user("creator1", "creator")
        auth_client(self.client, self.creator)
        self.client.post(
            reverse("document-list"),
            {"title": "HR Policy", "category": self.hr.id, "file": pdf_file()},
            format="multipart",
        )
        self.client.post(
            reverse("document-list"),
            {"title": "Finance Report", "category": self.finance.id, "file": pdf_file()},
            format="multipart",
        )

    def test_filter_by_status(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"), {"status": "draft"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)

    def test_invalid_status_returns_400(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"), {"status": "not-a-status"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_category_case_insensitive(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"), {"category": "hr"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "HR Policy")

    def test_filter_by_created_by(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"), {"created_by": self.creator.id})
        self.assertEqual(resp.data["count"], 2)

    def test_search_by_title(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"), {"search": "Finance"})
        self.assertEqual(resp.data["count"], 1)

    def test_pagination_response_shape(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"))
        self.assertIn("count", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)
        self.assertIn("results", resp.data)

    def test_page_size_capped(self):
        auth_client(self.client, self.admin)
        resp = self.client.get(reverse("document-list"), {"page_size": 1000})
        self.assertLessEqual(len(resp.data["results"]), 100)

    def test_query_count_constant_for_list(self):
        for i in range(5):
            self.client.post(
                reverse("document-list"),
                {"title": f"Doc {i}", "category": self.hr.id, "file": pdf_file()},
                format="multipart",
            )
        auth_client(self.client, self.admin)
        with self.assertNumQueries(3):
            self.client.get(reverse("document-list"))
