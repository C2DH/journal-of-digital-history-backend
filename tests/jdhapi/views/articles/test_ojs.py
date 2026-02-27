from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from jdhapi.models import Abstract, Article, Author, Issue
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class SendArticleToOJSTestCase(TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="testpass123"
        )

        # Create test article with abstract and authors
        self.abstract = Abstract.objects.create(
            pid="test-article-001",
            title="Test Article Title",
            abstract="Test article abstract",
            contact_email="author@test.com",
            contact_lastname="Doe",
        )

        self.author = Author.objects.create(
            firstname="John",
            lastname="Doe",
            email="author@test.com",
            affiliation="Test University",
            country="US",
            orcid="0000-0001-2345-6789",
        )

        self.abstract.authors.add(self.author)

        self.issue = Issue.objects.create(
            id=0,
            pid="jdh000",
            name="Issue 0",
            volume=1,
            issue=1,
            status=Issue.Status.PUBLISHED,
        )

        self.article = Article.objects.create(
            abstract=self.abstract,
            data={"title": "Test Article Title"},
            issue=self.issue,
        )

        self.url = "/api/articles/ojs/submission"
        self.valid_payload = {"pid": "test-article-001"}

    def test_send_article_to_ojs_not_authenticated(self):
        """Test that non-authenticated users cannot access the endpoint"""
        response = self.client.post(
            self.url, self.valid_payload, headers="", format="json"
        )
        # IsAdminUser returns 403, not 401, when not authenticated
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_send_article_to_ojs_not_admin(self):
        """Test that non-admin users cannot access the endpoint"""
        regular_user = User.objects.create_user(
            username="regular", email="regular@test.com", password="testpass123"
        )
        self.client.force_authenticate(user=regular_user)

        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("jdhapi.views.articles.ojs.generate_pdf_for_submission")
    @patch("jdhapi.views.articles.ojs.requests.post")
    @patch("jdhapi.views.articles.ojs.requests.put")
    def test_send_article_to_ojs_success(self, mock_put, mock_post, mock_pdf):
        """Test successful article submission to OJS"""
        self.client.force_authenticate(user=self.admin_user)

        # Mock PDF generation
        mock_pdf.return_value = b"fake_pdf_content"

        # Mock blank submission creation response
        mock_blank_submission_response = Mock()
        mock_blank_submission_response.status_code = 200
        mock_blank_submission_response.json.return_value = {
            "id": 123,
            "currentPublicationId": 456,
        }

        # Mock file upload response
        mock_upload_response = Mock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"id": 789}

        # Mock contributor creation response
        mock_contributor_response = Mock()
        mock_contributor_response.status_code = 201
        mock_contributor_response.json.return_value = {"id": 999}

        # Mock metadata assignment response
        mock_metadata_response = Mock()
        mock_metadata_response.status_code = 200
        mock_metadata_response.json.return_value = {"success": True}

        # Set up mock post to return different responses based on call order
        mock_post.side_effect = [
            mock_blank_submission_response,  # create_blank_submission
            mock_upload_response,  # upload_manuscript_to_ojs
            mock_contributor_response,  # create_contributor_in_ojs
        ]

        mock_put.return_value = mock_metadata_response

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(
            response.data["message"], "Article send successfully to OJS."
        )

        # Verify that the mocks were called
        self.assertEqual(mock_post.call_count, 3)
        self.assertEqual(mock_put.call_count, 1)
        mock_pdf.assert_called_once()

    @patch("jdhapi.views.articles.ojs.article_to_ojs_schema")
    def test_send_article_to_ojs_missing_pid(self, mock_schema):
        """Test that missing PID returns validation error"""
        self.client.force_authenticate(user=self.admin_user)

        # Mock schema validation to pass
        mock_schema.validate.return_value = None

        invalid_payload = {}
        response = self.client.post(self.url, invalid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("jdhapi.views.articles.ojs.article_to_ojs_schema")
    def test_send_article_to_ojs_article_not_found(self, mock_schema):
        """Test that non-existent article returns error"""
        self.client.force_authenticate(user=self.admin_user)

        # Mock schema validation to pass
        mock_schema.validate.return_value = None

        invalid_payload = {"pid": "non-existent-article"}
        response = self.client.post(self.url, invalid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch("jdhapi.views.articles.ojs.generate_pdf_for_submission")
    @patch("jdhapi.views.articles.ojs.requests.post")
    @patch("jdhapi.views.articles.ojs.article_to_ojs_schema")
    def test_send_article_to_ojs_missing_author_fields(
        self, mock_schema, mock_post, mock_pdf
    ):
        """Test that missing required author fields returns validation error"""
        self.client.force_authenticate(user=self.admin_user)

        # Mock PDF generation
        mock_pdf.return_value = b"fake_pdf_content"

        # Mock blank submission creation response
        mock_blank_submission_response = Mock()
        mock_blank_submission_response.status_code = 200
        mock_blank_submission_response.json.return_value = {
            "id": 123,
            "currentPublicationId": 456,
        }

        # Mock file upload response
        mock_upload_response = Mock()
        mock_upload_response.status_code = 200
        mock_upload_response.json.return_value = {"id": 789}

        # Mock schema validation to pass
        mock_schema.validate.return_value = None

        # Create author with missing required field
        incomplete_author = Author.objects.create(
            firstname="Jane",
            lastname="Smith",
            email="",  # Missing required field
            affiliation="Test University",
            country="US",
            orcid="0000-0001-2345-6789",
        )

        incomplete_abstract = Abstract.objects.create(
            pid="test-article-002",
            title="Test Article 2",
            abstract="Test abstract 2",
            contact_email="jane@test.com",
            contact_lastname="Smith",
        )
        incomplete_abstract.authors.add(incomplete_author)

        Article.objects.create(
            abstract=incomplete_abstract,
            data={"title": "Test Article 2"},
            issue=self.issue,
        )

        mock_post.side_effect = [
            mock_blank_submission_response,  # create_blank_submission
            mock_upload_response,  # upload_manuscript_to_ojs
        ]

        payload = {"pid": "test-article-002"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("jdhapi.views.articles.ojs.generate_pdf_for_submission")
    @patch("jdhapi.views.articles.ojs.requests.post")
    def test_send_article_to_ojs_upload_fails(self, mock_post, mock_pdf):
        """Test that failed manuscript upload returns error"""
        self.client.force_authenticate(user=self.admin_user)

        mock_pdf.return_value = b"fake_pdf_content"

        # Mock successful blank submission
        mock_blank_submission = Mock()
        mock_blank_submission.status_code = 201
        mock_blank_submission.json.return_value = {
            "id": 123,
            "currentPublicationId": 456,
        }

        # Mock failed upload
        mock_upload_fail = Mock()
        mock_upload_fail.status_code = 400
        mock_upload_fail.text = "Upload failed"

        mock_post.side_effect = [mock_blank_submission, mock_upload_fail]

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    @patch("jdhapi.views.articles.ojs.generate_pdf_for_submission")
    @patch("jdhapi.views.articles.ojs.requests.post")
    @patch("jdhapi.views.articles.ojs.requests.put")
    def test_send_article_to_ojs_metadata_assignment_fails(
        self, mock_put, mock_post, mock_pdf
    ):
        """Test that failed metadata assignment returns error"""
        self.client.force_authenticate(user=self.admin_user)

        mock_pdf.return_value = b"fake_pdf_content"

        # Mock successful responses for initial calls
        mock_blank_submission = Mock()
        mock_blank_submission.status_code = 201
        mock_blank_submission.json.return_value = {
            "id": 123,
            "currentPublicationId": 456,
        }

        mock_upload = Mock()
        mock_upload.status_code = 200
        mock_upload.json.return_value = {"id": 789}

        mock_contributor = Mock()
        mock_contributor.status_code = 201
        mock_contributor.json.return_value = {"id": 999}

        mock_post.side_effect = [mock_blank_submission, mock_upload, mock_contributor]

        # Mock failed metadata assignment
        mock_metadata_fail = Mock()
        mock_metadata_fail.status_code = 400
        mock_metadata_fail.text = "Metadata assignment failed"

        mock_put.return_value = mock_metadata_fail

        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
