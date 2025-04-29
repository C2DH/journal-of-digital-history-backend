from rest_framework.test import APITestCase
from rest_framework import status
from django.test import Client
from jdhapi.models import Abstract, Author, Dataset, CallOfPaper
from django.urls import reverse
from datetime import date


class SubmitAbstractTestCase(APITestCase):
    def setUp(self):
        self.call_of_paper = CallOfPaper.objects.create(
            title="Test Call for Paper",
            folder_name="test-call",
            deadline_abstract=date.today(),
            deadline_article=date.today(),
        )

        self.valid_payload = {
            "title": "Test Abstract",
            "abstract": (
                "The quick brown fox jumps over the lazy dog, "
                "demonstrating the versatility of the English language"
                "in concise communication."
            ),
            "callForPapers": "test-call",
            "authors": [
                {
                    "firstname": "Jane",
                    "lastname": "Smith",
                    "affiliation": "Another University",
                    "email": "jane.smith@example.com",
                    "orcidUrl": "https://orcid.org/0000-0000-0000-0000",
                    "githubId": "janesmith",
                    "blueskyId": "jane.bsky.social",
                    "facebookId": "jane.smith",
                    "primaryContact": True,
                }
            ],
            "datasets": [
                {
                    "link": "https://example.com/dataset1",
                    "description": "Dataset 1 description",
                }
            ],
            "dateCreated": date.today(),
            "dateLastModified": date.today(),
            "languagePreference": "Default",
            "termsAccepted": True,
        }

        self.invalid_payload_missing_github_id = {
            "title": "Test Abstract",
            "abstract": (
                "The quick brown fox jumps over the lazy dog, "
                "demonstrating the versatility of the English language"
                "in concise communication."
            ),
            "callForPapers": "test-call",
            "authors": [
                {
                    "firstname": "Jane",
                    "lastname": "Smith",
                    "affiliation": "Another University",
                    "email": "jane.smith@example.com",
                    "orcidUrl": "https://orcid.org/0000-0000-0000-0000",
                    "githubId": "",
                    "blueskyId": "jane.bsky.social",
                    "facebookId": "jane.smith",
                    "primaryContact": True,
                }
            ],
            "datasets": [
                {
                    "link": "https://example.com/dataset1",
                    "description": "Dataset 1 description",
                }
            ],
            "dateCreated": date.today(),
            "dateLastModified": date.today(),
            "languagePreference": "Default",
            "termsAccepted": True,
        }

        self.invalid_payload = {
            "title": "Test Abstract",
            "abstract": "This is a test abstract.",
            "contact": [],
        }

    def test_submit_abstract_valid_payload(self):
        """Test submitting an abstract with a valid payload."""
        url = reverse("submit-abstract")
        c = Client()
        response = c.post(
            url,
            self.valid_payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Abstract.objects.count(), 1)
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(Dataset.objects.count(), 1)
        self.assertEqual(response.data["title"], self.valid_payload["title"])

    def test_submit_abstract_invalid_payload(self):
        """Test submitting an abstract with an invalid payload."""
        url = reverse("submit-abstract")
        c = Client()
        response = c.post(
            url,
            self.invalid_payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(Abstract.objects.count(), 0)
        self.assertEqual(Author.objects.count(), 0)
        response = c.post(
            url,
            self.invalid_payload_missing_github_id,
            content_type="application/json",
        )

    # def test_submit_abstract_invalid_payload_missing_github_id(self):
    #     """
    #     Test submitting an abstract with an invalid payload
    #     (missing GitHub ID).
    #     """
    #     url = reverse("submit-abstract")
    #     c = Client()
    #     response = c.post(
    #         url,
    #         self.invalid_payload_missing_github_id,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    #     self.assertIn("error", response.data)
    #     self.assertEqual(
    #         response.data["message"],
    #         "At least one author must have a GitHub ID.",
    #     )
    #     self.assertEqual(Abstract.objects.count(), 0)
    #     self.assertEqual(Author.objects.count(), 0)
    #     self.assertEqual(Dataset.objects.count(), 0)

    # def test_update_existing_author(self):
    #     """Test that an existing author's information is updated."""
    #     self.existing_author = Author.objects.create(
    #         orcid="https://orcid.org/0000-0000-0000-0000",
    #         lastname="Existing",
    #         firstname="Author",
    #         email="existing.author@example.com",
    #         affiliation="Existing University",
    #         github_id="existinggithub",
    #         bluesky_id="existing.bsky.social",
    #         facebook_id="existing.author",
    #     )

    #     url = reverse("submit-abstract")
    #     response = self.client.post(url, self.valid_payload, format="json")

    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     # Ensure no new author is created
    #     self.assertEqual(Author.objects.count(), 1)

    #     updated_author = Author.objects.get(
    #         orcid="https://orcid.org/0000-0000-0000-0000"
    #     )
    #     self.assertEqual(updated_author.firstname, "Jane")
    #     self.assertEqual(updated_author.lastname, "Smith")
    #     self.assertEqual(updated_author.email, "jane.smith@example.com")
    #     self.assertEqual(updated_author.affiliation, "Another University")
    #     self.assertEqual(updated_author.github_id, "janesmith")
    #     self.assertEqual(updated_author.bluesky_id, "jane.bsky.social")
    #     self.assertEqual(updated_author.facebook_id, "jane.smith")
