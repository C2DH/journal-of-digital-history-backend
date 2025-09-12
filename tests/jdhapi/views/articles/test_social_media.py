import json
import unittest
from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from jsonschema.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from jdhapi.views.articles.social_media import bluesky_campaign, facebook_campaign


User = get_user_model()


class SocialMediaViewsTestCase(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin", password="adminpass", is_staff=True
        )
        self.client = APIClient()
        self.client.login(username="admin", password="adminpass")

        self.payload = {
            "repository_url": "https://github.com/owner/repo",
            "article_url": "https://example.com/article",
            "schedule_main": [],
        }
        self.url_bluesky = reverse("articles-bluesky")
        self.url_facebook = reverse("articles-facebook")

    @patch("jdhapi.views.articles.social_media.launch_social_media_bluesky")
    def test_bluesky_campaign_success(self, mock_launch):
        mock_launch.return_value = {"message": "ok", "scheduled_jobs": 0}

        res = self.client.post(self.url_bluesky, data=self.payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["data"] == {"message": "ok", "scheduled_jobs": 0}

    @patch("jdhapi.views.articles.social_media.launch_social_media_bluesky")
    def test_bluesky_campaign_value_error(self, mock_launch):
        mock_launch.side_effect = ValueError("bad input")

        res = self.client.post(self.url_bluesky, data=self.payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["error"] == "ValueError"

    @patch("jdhapi.views.articles.social_media.launch_social_media_bluesky")
    def test_bluesky_campaign_validation_error(self, mock_launch):
        mock_launch.side_effect = ValidationError("schema")

        res = self.client.post(self.url_bluesky, data=self.payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["error"] == "Invalid data format"

    @patch("jdhapi.views.articles.social_media.launch_social_media_bluesky")
    def test_bluesky_campaign_internal_error(self, mock_launch):
        mock_launch.side_effect = Exception("boom")
        res = self.client.post(self.url_bluesky, data=self.payload, format="json")

        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert res.data["error"] == "InternalError"

    def test_bluesky_campaign_permission_denied(self):
        User.objects.create_user(username="user", password="userpass", is_staff=False)
        self.client.logout()
        self.client.login(username="user", password="userpass")

        res = self.client.post(self.url_bluesky, data=self.payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    # Facebook tests
    @patch("jdhapi.views.articles.social_media.launch_social_media_facebook")
    def test_facebook_campaign_success(self, mock_launch):
        mock_launch.return_value = {"post_id": "123", "scheduled_time": None}
        res = self.client.post(self.url_facebook, data=self.payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["data"] == {"post_id": "123", "scheduled_time": None}

    @patch("jdhapi.views.articles.social_media.launch_social_media_facebook")
    def test_facebook_campaign_value_error(self, mock_launch):
        mock_launch.side_effect = ValueError("bad input")
        res = self.client.post(self.url_facebook, data=self.payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["error"] == "ValueError"

    @patch("jdhapi.views.articles.social_media.launch_social_media_facebook")
    def test_facebook_campaign_validation_error(self, mock_launch):
        mock_launch.side_effect = ValidationError("schema")
        res = self.client.post(self.url_facebook, data=self.payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.data["error"] == "Invalid data format"

    @patch("jdhapi.views.articles.social_media.launch_social_media_facebook")
    def test_facebook_campaign_internal_error(self, mock_launch):
        mock_launch.side_effect = Exception("boom")
        res = self.client.post(self.url_facebook, data=self.payload, format="json")
        assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert res.data["error"] == "InternalError"

    def test_facebook_campaign_permission_denied(self):
        User.objects.create_user(username="user", password="userpass", is_staff=False)
        self.client.logout()
        self.client.login(username="user", password="userpass")

        res = self.client.post(self.url_facebook, data=self.payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
