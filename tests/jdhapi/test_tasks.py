from unittest.mock import Mock, patch

from django.test import TestCase

from jdhapi.models import Abstract, Article, Issue
from jdhapi.tasks import get_github_issue_url_for_article


class TestGetGithubIssueUrlForArticle(TestCase):
    def setUp(self):
        self.abstract = Abstract.objects.create(pid="TESTPID123", title="t")
        self.issue = Issue.objects.create(name="i", publication_date="2024-10-21T14:37:06+02:00")
        self.article = Article.objects.create(abstract=self.abstract, issue=self.issue)

    @patch("jdhapi.tasks.requests.get")
    def test_sets_github_issue_on_match(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: [{"body": f"fixes {self.abstract.pid}", "html_url": "https://github.com/x/issues/1"}],
        )
        get_github_issue_url_for_article(self.article.pk)
        self.article.refresh_from_db()
        self.assertEqual(self.article.github_issue, "https://github.com/x/issues/1")