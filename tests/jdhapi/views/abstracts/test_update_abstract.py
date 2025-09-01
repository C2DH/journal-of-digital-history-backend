from django.contrib.auth import get_user_model
from django.urls import reverse
from jdhapi.models import Abstract
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch


class UpdateAbstractStatusTestCase(APITestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_user(
            username="admin", password="adminpass", is_staff=True
        )
        self.client = APIClient()
        self.client.login(username="admin", password="adminpass")
        self.abstract1 = Abstract.objects.create(
            pid="testpid1",
            title="Test Abstract 1",
            contact_email="test1@example.com",
            status=Abstract.Status.SUBMITTED,
        )
        self.abstract2 = Abstract.objects.create(
            pid="testpid2",
            title="Test Abstract 2",
            contact_email="test2@example.com",
            status=Abstract.Status.SUBMITTED,
        )
        self.single_url = reverse(
            "abstract-change-status-with-email", args=[self.abstract1.pid]
        )
        self.bulk_url = reverse("abstract-change-status")
        self.single_data = {
            "from": "admin@example.com",
            "to": "test1@example.com",
            "subject": "Test Subject",
            "body": "Test message",
            "status": "accepted",
        }
        self.bulk_data = {
            "pids": [self.abstract1.pid, self.abstract2.pid],
            "status": "declined",
        }

    @patch("jdhapi.views.abstracts.update_abstract.send_mail")
    def test_update_abstract_status_with_email_success(self, mock_send_mail):
        mock_send_mail.return_value = 1
        response = self.client.patch(self.single_url, self.single_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["pid"], self.abstract1.pid)
        self.assertEqual(response.data["data"]["new_status"], Abstract.Status.ACCEPTED)

    @patch("jdhapi.views.abstracts.update_abstract.send_mail")
    def test_update_abstract_status_with_email_invalid_schema(self, mock_send_mail):
        data = self.single_data.copy()
        data["subject"] = 12345  # Should be a string
        response = self.client.patch(self.single_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_update_abstract_status_with_email_not_found(self):
        url = reverse("abstract-change-status-with-email", args=["doesnotexist"])
        response = self.client.patch(url, self.single_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    def test_update_abstract_status_bulk_success(self):
        response = self.client.patch(self.bulk_url, self.bulk_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(
            response.data["data"][0]["new_status"], Abstract.Status.DECLINED
        )
        self.assertEqual(
            response.data["data"][1]["new_status"], Abstract.Status.DECLINED
        )

    def test_update_abstract_status_bulk_missing_pids(self):
        data = {"status": "declined"}
        response = self.client.patch(self.bulk_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_update_abstract_status_bulk_not_found(self):
        data = {"pids": ["doesnotexist"], "status": "declined"}
        response = self.client.patch(self.bulk_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
