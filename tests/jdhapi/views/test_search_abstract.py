from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from jdhapi.models import Abstract, Article, Issue  # adjust your app label
from django.utils import timezone


class ArticleSearchTestCase(APITestCase):
    def setUp(self):
        # Create an Issue since Article.issue is required
        self.issue = Issue.objects.create(pid="ISSUE1", publication_date=timezone.now())

        # Abstract that will match by title
        self.abs_title = Abstract.objects.create(
            pid="TITLE123",
            title="Deep Learning Advances",
            contact_affiliation="Uni A",
            contact_lastname="Doe",
            contact_firstname="John",
        )
        Article.objects.create(
            abstract=self.abs_title,
            issue=self.issue,
            publication_date=timezone.now(),
            status="PUBLISHED",
        )

        # Abstract that will match by PID
        self.abs_pid = Abstract.objects.create(
            pid="PID456",
            title="Some Other Topic",
            contact_affiliation="Uni B",
            contact_lastname="Smith",
            contact_firstname="Jane",
        )
        Article.objects.create(
            abstract=self.abs_pid,
            issue=self.issue,
            publication_date=timezone.now(),
            status="PUBLISHED",
        )

        self.url = reverse("article-list")

    def test_search_matches_abstract_title(self):
        test_name = "test_search_matches_abstract_title"
        try:
            resp = self.client.get(self.url, {"search": "Deep Learning"})
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.data.get("results", resp.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["abstract"]["pid"], "TITLE123")
            print(f"{test_name}: SUCCESS - Found by abstract title")
        except AssertionError as e:
            print(f"{test_name}: FAILED - {e}")
            raise

    def test_search_matches_exact_pid(self):
        test_name = "test_search_matches_exact_pid"
        try:
            resp = self.client.get(self.url, {"search": "PID456"})
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.data.get("results", resp.data)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["abstract"]["pid"], "PID456")
            print(f"{test_name}: SUCCESS - Found by exact PID")
        except AssertionError as e:
            print(f"{test_name}: FAILED - {e}")
            raise

    def test_search_no_query_returns_all(self):
        test_name = "test_search_no_query_returns_all"
        try:
            resp = self.client.get(self.url)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.data.get("results", resp.data)
            self.assertEqual(len(data), 2)
            print(f"{test_name}: SUCCESS - Returned all articles when no search term")
        except AssertionError as e:
            print(f"{test_name}: FAILED - {e}")
            raise

    def test_search_no_matches(self):
        test_name = "test_search_no_matches"
        try:
            resp = self.client.get(self.url, {"search": "nonexistent"})
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.data.get("results", resp.data)
            self.assertEqual(data, [])
            print(f"{test_name}: SUCCESS - Returned empty list when no matches")
        except AssertionError as e:
            print(f"{test_name}: FAILED - {e}")
            raise
