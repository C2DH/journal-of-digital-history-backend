from unittest.mock import Mock, patch

from django.test import Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CheckGitHubIDTestCase(APITestCase):
    def setUp(self):
        self.valid_username = "octocat"
        self.invalid_username = "nonexistentuser"
        self.github_api_url = "https://api.github.com/users/"

    @patch("jdhapi.views.check_github_id.requests.get")
    def test_valid_github_user(self, mock_get):
        """
        Test that a valid GitHub username returns a 200 response with user data.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": self.valid_username}
        mock_get.return_value = mock_response

        url = reverse("check-github-id", args=[self.valid_username])
        c = Client()
        response = c.get(url)

        mock_get.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exists"], True)
        self.assertEqual(response.data["data"]["login"], self.valid_username)

    @patch("jdhapi.views.check_github_id.requests.get")
    def test_invalid_github_user(self, mock_get):
        """
        Test that an invalid GitHub username returns a 404 response.
        """
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        url = reverse("check-github-id", args=[self.invalid_username])
        c = Client()
        response = c.get(url)

        mock_get.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["exists"], False)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"],
            f"GitHub user '{self.invalid_username}' not found.",
        )
