from unittest.mock import Mock, patch

import requests
from django.test import TestCase, override_settings
from jdhapi.utils.github_repository import _github_issue_tag_user


@override_settings(GITHUB_API_TOKEN="fake-token")
class GithubIssueTagUserTestCase(TestCase):
    def setUp(self):
        self.username = "octocat"
        self.message = "This article has switched to Design Review."
        self.github_issue_url = "https://github.com/owner/repo/issues/5"

    @patch("jdhapi.utils.github_repository.requests.post")
    def test_posts_comment_with_correct_url_headers_and_body(self, mock_post):
        """
        Test that the function builds the correct GitHub API URL, headers,
        and body, and returns the response on success.
        """
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        response = _github_issue_tag_user(
            self.username, self.message, self.github_issue_url
        )

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(
            args[0],
            "https://api.github.com/repos/owner/repo/issues/5/comments",
        )
        self.assertEqual(
            kwargs["headers"], {"Authorization": "Bearer fake-token"}
        )
        self.assertEqual(
            kwargs["json"],
            {"body": f"@{self.username} - {self.message}"},
        )
        self.assertIs(response, mock_response)
        self.assertEqual(response.status_code, 201)

    @patch("jdhapi.utils.github_repository.requests.post")
    def test_returns_error_response_on_request_exception(self, mock_post):
        """
        Test that a requests exception is caught and a 500 error Response
        is returned instead of propagating the exception.
        """
        mock_post.side_effect = requests.exceptions.RequestException("boom")

        response = _github_issue_tag_user(
            self.username, self.message, self.github_issue_url
        )

        mock_post.assert_called_once()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["error"], "Failed to connect to GitHub API.")
        self.assertEqual(response.data["details"], "boom")