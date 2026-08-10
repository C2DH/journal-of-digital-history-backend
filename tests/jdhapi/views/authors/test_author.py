from django.contrib.auth import get_user_model
from django.test import TestCase
from jdhapi.models.abstract import Abstract
from jdhapi.models.author import Author
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class TestAuthorCreation(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )

        self.author_complete = Author.objects.create(
            email="johndoe@example.com",
            lastname="Doe",
            firstname="John",
            orcid="0000-0000-0000-0000",
            affiliation="University",
            city="City",
            country="US",
        )
        self.author_uncomplete = Author.objects.create(
            lastname="Doe",
            firstname="Alice",
            affiliation="University",
        )

        # 4 linked abstracts for John: 2 accepted, 1 published, 1 submitted
        a1 = self._create_abstract("A1", "ACCEPTED")
        a2 = self._create_abstract("A2", "ACCEPTED")
        a3 = self._create_abstract("A3", "PUBLISHED")
        a4 = self._create_abstract("A4", "SUBMITTED")
        for abs_obj in (a1, a2, a3, a4):
            abs_obj.authors.add(self.author_complete)

    def _create_abstract(self, title, status_value):
        return Abstract.objects.create(
            title=title,
            status=status_value,
            abstract="Test abstract body",
            contact_affiliation="University",
            contact_email="contact@test.com",
            contact_lastname="Doe",
            contact_firstname="John",
        )

    def test_cannot_access_author_api_if_not_authenticated(self):
        response = self.client.get("/api/authors/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_author_api(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get("/api/authors/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        authors_by_firstname = {a["firstname"]: a for a in response.data["results"]}
        author_complete = authors_by_firstname["John"]
        author_uncomplete = authors_by_firstname["Alice"]

        self.assertEqual(author_complete["country"], "US")
        self.assertEqual(author_uncomplete["country"], "")

        self.assertEqual(author_complete["abstracts"], 4)
        self.assertEqual(author_complete["accepted"], 2)
        self.assertEqual(author_complete["published"], 1)