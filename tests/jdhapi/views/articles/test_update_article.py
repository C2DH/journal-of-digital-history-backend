from django.contrib.auth import get_user_model
from django.urls import reverse
from jdhapi.models import Abstract, Article, Issue
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class UpdateArticleStatusTestCase(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin", password="adminpass", is_staff=True
        )
        self.client = APIClient()
        self.client.login(username="admin", password="adminpass")
        self.issue = Issue.objects.create(
            id=1,
            pid="issuepid1",
            name="Test Issue 1",
            # Add other required fields for Issue here
        )
        self.abstract1 = Abstract.objects.create(
            pid="testpid1",
            title="Test Abstract 1",
            contact_email="test1@example.com",
        )
        self.abstract2 = Abstract.objects.create(
            pid="testpid2",
            title="Test Abstract 2",
            contact_email="test2@example.com",
        )
        self.article1 = Article.objects.create(
            abstract=self.abstract1,
            status=Article.Status.TECHNICAL_REVIEW,
            issue=self.issue,
            data={"title": "Article 1"},
        )
        self.article2 = Article.objects.create(
            abstract=self.abstract2,
            status=Article.Status.DESIGN_REVIEW,
            issue=self.issue,
            data={"title": "Article 2"},
        )
        self.url = reverse("article-change-status")
        self.valid_data = {
            "pids": [self.abstract1.pid, self.abstract2.pid],
            "status": "archived",
        }

    def test_update_article_status_success(self):
        response = self.client.patch(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(response.data["data"][0]["new_status"], "ARCHIVED")
        self.assertEqual(response.data["data"][1]["new_status"], "ARCHIVED")

    def test_update_article_status_missing_pids(self):
        data = {"status": "archived"}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_update_article_status_not_found(self):
        data = {"pids": ["doesnotexist"], "status": "archived"}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    def test_update_article_status_invalid_schema(self):
        data = {
            "pids": [self.abstract1.pid],
            "status": 12345,
        }  # status should be string
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
