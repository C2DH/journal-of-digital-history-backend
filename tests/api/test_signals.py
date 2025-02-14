from django.test import TestCase
from jdhapi.models import Article, Abstract, Issue
from unittest.mock import patch, Mock
from django.utils import timezone

date = timezone.make_aware(timezone.datetime(2023, 10, 1))


class TestSignal(TestCase):
    def setUp(self):

        self.abstract = Abstract.objects.create(
            title="Test Abstract",
            abstract="This is a test abstract",
            contact_orcid="0000-0000-0000-0000",
            contact_affiliation="Test Affiliation",
            contact_email="test@example.com",
            contact_lastname="Doe",
            contact_firstname="John",
        )
        self.issue = Issue.objects.create(
            name="Test Issue",
            publication_date=date,
        )

    def test_validate_urls_for_article_submission_valid_urls(self):
        repository_url = "https://github.com/jdh-observer/repositoryUrl"
        notebook_url = "JTJGcHJveHktZ2l0aHVidXNlcmNvbnRlbnQlMkZqZGgtb2JzZXJ2ZXIlMkZyZXBvc2l0b3J5VXJsJTJGbWFpbiUyRmFydGljbGUuaXB5bmI="

        with patch("jdhapi.signals.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            self.article = Article.objects.create(
                status=Article.Status.DRAFT,
                notebook_url=notebook_url,
                repository_url=repository_url,
                notebook_path="article.ipynb",
                abstract=self.abstract,
                publication_date=date,
                issue=self.issue,
            )
            self.article.save()

            self.assertEqual(self.article.notebook_url, notebook_url)
            self.assertEqual(self.article.repository_url, repository_url)
