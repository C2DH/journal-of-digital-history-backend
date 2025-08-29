from django.contrib.auth import get_user_model
from django.urls import reverse
from jdhapi.models import Abstract
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch


class ModifyAbstractTestCase(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin", password="adminpass", is_staff=True
        )
        self.client = APIClient()
        self.client.login(username="admin", password="adminpass")
        self.abstract = Abstract.objects.create(
            pid="testpid",
            title="Test Abstract",
            contact_email="test@example.com",
            status=Abstract.Status.SUBMITTED,
        )
        self.url = reverse(
            "abstract-change-status-with-email", args=[self.abstract.pid]
        )
        self.data = {
            "from": "admin@example.com",
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test message",
            "status": "accepted",
        }

    @patch("jdhapi.views.abstracts.update_abstract.send_mail")
    def test_modify_abstract_success(self, mock_send_mail):
        mock_send_mail.return_value = 1  # Simulate successful send
        response = self.client.patch(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["pid"], self.abstract.pid)
        self.assertEqual(response.data["data"]["title"], self.abstract.title)
        self.assertEqual(response.data["data"]["new_status"], Abstract.Status.ACCEPTED)

    @patch("jdhapi.views.abstracts.update_abstract.send_mail")
    def test_invalid_json_schema_type(self, mock_send_mail):
        data = self.data.copy()
        data["subject"] = 12345  # Should be a string, not an int
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_missing_pid_in_db(self):
        # Use a PID that doesn't exist in DB
        url = reverse("abstract-change-status-with-email", args=["invalid-pid"])
        response = self.client.patch(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("No Abstract matches the given query.", response.data["details"])

    def test_abstract_not_found(self):
        url = reverse("abstract-change-status-with-email", args=["doesnotexist"])
        response = self.client.patch(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    @patch("jdhapi.views.abstracts.update_abstract.EmailConfigurationForm")
    def test_invalid_email_data(self, mock_email_form):
        # Simulate invalid email form
        mock_email_form.return_value.is_valid.return_value = False
        mock_email_form.return_value.errors = {"subject": ["This field is required."]}
        response = self.client.patch(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    @patch(
        "jdhapi.views.abstracts.update_abstract.send_mail",
        side_effect=Exception("SMTP error"),
    )
    def test_send_mail_exception(self, mock_send_mail):
        response = self.client.patch(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
