from django.test import TestCase
from jdhapi.models import Article, Abstract


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
        self.article = Article.objects.create(
            status=Article.Status.DRAFT,
            notebook_url="notebookUrl",
            repository_url="https://example.com/repositoryUrl",
            abstract=self.abstract,
            publication_date="2023-10-01",
        )

    def test_validate_urls_for_article_submission_valid_urls(self):
        self.article = Article.objects.create(
            status=Article.Status.DRAFT,
            notebook_url="notebookUrl",
            repository_url="https://example.com/repositoryUrl",
            abstract=self.abstract,
            publication_date="2023-10-01",
        )
        breakpoint()
        self.article.save()

        self.assertEqual(self.article.notebook_url, "notebookUrl")
        self.assertEqual(
            self.article.repository_url, "https://example.com/repositoryUrl"
        )
