from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from jdhapi.models import Abstract
from django.contrib.auth import get_user_model


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
        self.url = reverse("modify-abstract", args=[self.abstract.pid])
        self.data = {
            "from": "admin@example.com",
            "to": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message",
            "status": "ACCEPTED",
        }

    @patch("jdhapi.views.modify_abstract.send_mail")
    def test_modify_abstract_success(self, mock_send_mail):
        mock_send_mail.return_value = 1  # Simulate successful send
        response = self.client.put(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["pid"], self.abstract.pid)
        self.assertEqual(response.data["data"]["title"], self.abstract.title)
        self.assertEqual(response.data["data"]["new_status"], Abstract.Status.ACCEPTED)
