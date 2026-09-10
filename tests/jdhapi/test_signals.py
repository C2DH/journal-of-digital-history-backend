from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from jdhapi.models import Abstract, Article, Issue

from .fixtures.fixture_signals import (
    date,
    false_notebook_url,
    false_repository_url,
    notebook_url,
    notebook_url_skim,
    repository_url,
)


class TestSignal(TestCase):

    def setUp(self):
        self.abstract = Abstract.objects.create(
            title="Test Abstract",
            abstract="This is a test abstract",
            contact_affiliation="Test Affiliation",
            contact_email="test@example.com",
            contact_lastname="Doe",
            contact_firstname="John",
        )
        self.issue = Issue.objects.create(
            name="Test Issue",
            publication_date=date,
        )

    def create_article(self, notebook_url, repository_url, notebook_path):
        return Article.objects.create(
            status=Article.Status.DRAFT,
            notebook_url=notebook_url,
            repository_url=repository_url,
            notebook_path=notebook_path,
            publication_date=date,
            abstract=self.abstract,
            issue=self.issue,
        )

    @patch("jdhapi.signals.get_github_issue_url_for_article.delay")
    def test_validate_urls_for_article_submission(self, mock_delay):

        with patch("jdhapi.signals.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            article = self.create_article(
                notebook_url,
                repository_url,
                "article.ipynb",
            )
            article.save()

            self.assertEqual(article.notebook_url, notebook_url)
            self.assertEqual(article.repository_url, repository_url)

    @patch("jdhapi.signals.get_github_issue_url_for_article.delay")
    def test_validate_urls_for_skim_article_submission(self, delay):

        with patch("jdhapi.signals.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            article = self.create_article(
                notebook_url_skim,
                repository_url,
                "skim-article.ipynb",
            )
            article.save()

            self.assertEqual(article.notebook_url, notebook_url_skim)
            self.assertEqual(article.repository_url, repository_url)

    def test_false_repository_url_for_article_submission(self):

        with patch("jdhapi.signals.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            with self.assertRaises(ValidationError):
                article = self.create_article(
                    notebook_url,
                    false_repository_url,
                    "article.ipynb",
                )
                article.save()

    def test_false_notebook_url_for_article_submission(self):

        with patch("jdhapi.signals.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            with self.assertRaises(ValidationError):
                article = self.create_article(
                    false_notebook_url,
                    repository_url,
                    "article.ipynb",
                )
                article.save()
