from django.test import Client
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


class CheckGitHubIDTestCase(APITestCase):
    def setUp(self):
        self.valid_username = "octocat"
        self.invalid_username = "nonexistentuser"
        self.github_api_url = "https://api.github.com/users/"

    def test_valid_github_user(self):
        """
        Test that a valid GitHub username returns a 200 response with user data.
        """
        url = reverse("check-github-id", args=[self.valid_username])
        c = Client()
        response = c.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["exists"], True)
        self.assertEqual(response.data["data"]["login"], self.valid_username)

    def test_invalid_github_user(self):
        """
        Test that an invalid GitHub username returns a 404 response.
        """
        url = reverse("check-github-id", args=[self.invalid_username])
        c = Client()
        response = c.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["exists"], False)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"],
            f"GitHub user '{self.invalid_username}' not found.",
        )
