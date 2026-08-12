from django.contrib.auth import get_user_model
from django.test import TestCase
from jdhapi.models.abstract import Abstract
from jdhapi.models.author import Author
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class TestAuthorStats(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="testpass123",
        )

        self.author_one = Author.objects.create(
            lastname="One",
            firstname="Author",
            affiliation="University A",
        )
        self.author_two = Author.objects.create(
            lastname="Two",
            firstname="Author",
            affiliation="University B",
        )
        self.author_three = Author.objects.create(
            lastname="Three",
            firstname="Author",
            affiliation="University C",
        )

        # author_one: 1 abstract -> first-time author
        abstract_1 = Abstract.objects.create(
            title="Abstract 1",
            abstract="Body 1",
            contact_affiliation="University A",
            contact_email="a@example.com",
            contact_lastname="One",
            contact_firstname="Author",
        )
        abstract_1.authors.add(self.author_one)

        # author_two: 2 abstracts -> returning author
        abstract_2 = Abstract.objects.create(
            title="Abstract 2",
            abstract="Body 2",
            contact_affiliation="University B",
            contact_email="b@example.com",
            contact_lastname="Two",
            contact_firstname="Author",
        )
        abstract_2.authors.add(self.author_two)

        abstract_3 = Abstract.objects.create(
            title="Abstract 3",
            abstract="Body 3",
            contact_affiliation="University B",
            contact_email="b2@example.com",
            contact_lastname="Two",
            contact_firstname="Author",
        )
        abstract_3.authors.add(self.author_two)

        # author_three: 3 abstracts -> returning author
        abstract_4 = Abstract.objects.create(
            title="Abstract 4",
            abstract="Body 4",
            contact_affiliation="University C",
            contact_email="c@example.com",
            contact_lastname="Three",
            contact_firstname="Author",
        )
        abstract_4.authors.add(self.author_three)

        abstract_5 = Abstract.objects.create(
            title="Abstract 5",
            abstract="Body 5",
            contact_affiliation="University C",
            contact_email="c2@example.com",
            contact_lastname="Three",
            contact_firstname="Author",
        )
        abstract_5.authors.add(self.author_three)

        abstract_6 = Abstract.objects.create(
            title="Abstract 6",
            abstract="Body 6",
            contact_affiliation="University C",
            contact_email="c3@example.com",
            contact_lastname="Three",
            contact_firstname="Author",
        )
        abstract_6.authors.add(self.author_three)

    def test_get_authors_stats(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/authors/stats")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_authors_stats_returning(self):

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/authors/stats")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["first-time_vs_returning"],
            [
                {"id": 0, "value": 1, "label": "First time authors"},
                {"id": 1, "value": 2, "label": "Returning authors"},
            ],
        )

    def test_get_authors_stats_coauthorship(self):

        self.author_co_one = Author.objects.create(
            lastname="One",
            firstname="Author",
            affiliation="University A",
        )
        self.author_co_two = Author.objects.create(
            lastname="Two",
            firstname="Author",
            affiliation="University B",
        )
        self.author_co_three = Author.objects.create(
            lastname="Three",
            firstname="Author",
            affiliation="University C",
        )
        self.author_co_four = Author.objects.create(
            lastname="Four",
            firstname="Author",
            affiliation="University D",
        )

        # coauthorship distribution
        co_1 = Abstract.objects.create(
            title="Co Abstract 1",
            abstract="Solo article",
            contact_affiliation="University A",
            contact_email="solo@example.com",
            contact_lastname="One",
            contact_firstname="Author",
        )
        co_1.authors.add(self.author_co_one)

        co_2 = Abstract.objects.create(
            title="Co Abstract 2",
            abstract="Two authors",
            contact_affiliation="University B",
            contact_email="pair@example.com",
            contact_lastname="Two",
            contact_firstname="Author",
        )
        co_2.authors.add(self.author_co_two, self.author_co_three)

        co_3 = Abstract.objects.create(
            title="Co Abstract 3",
            abstract="Three authors",
            contact_affiliation="University C",
            contact_email="tri@example.com",
            contact_lastname="Three",
            contact_firstname="Author",
        )
        co_3.authors.add(self.author_co_one, self.author_co_two, self.author_co_four)

        co_4 = Abstract.objects.create(
            title="Co Abstract 4",
            abstract="Four authors",
            contact_affiliation="University D",
            contact_email="many@example.com",
            contact_lastname="Four",
            contact_firstname="Author",
        )
        co_4.authors.add(
            self.author_co_one,
            self.author_co_two,
            self.author_co_three,
            self.author_co_four,
        )

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get("/api/authors/stats")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # value = 7 because you have previous authors from 'returning'test
        self.assertEqual(
            response.data["coauthorship"],
            [
                {"id": 0, "value": 7, "label": "1 author"},
                {"id": 1, "value": 1, "label": "2 authors"},
                {"id": 2, "value": 1, "label": "3 authors"},
                {"id": 3, "value": 1, "label": "4+ authors"},
            ],
        )
