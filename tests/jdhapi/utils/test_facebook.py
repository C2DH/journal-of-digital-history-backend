import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from jdhapi.utils import facebook


class TestFacebookLaunch(unittest.TestCase):
    def setUp(self):
        self.tweets_md = "\n".join(
            [
                "Post thread:",
                "1. First post text",
                "2. Second post text",
                "3. Third post text",
            ]
        ).encode("utf-8")
        self.repo_url = "https://github.com/owner/repo"
        self.article_link = "https://example.com/article"

    @patch("jdhapi.utils.facebook.parse_repo_url", return_value=("owner", "repo"))
    @patch("jdhapi.utils.facebook.get_default_branch", return_value="main")
    @patch("jdhapi.utils.facebook.fetch_file_bytes")
    @patch("jdhapi.utils.facebook.parse_tweets_md")
    @patch("jdhapi.utils.facebook.fb_upload_photo")
    @patch("jdhapi.utils.facebook.fb_post_feed")
    def test_launch_without_schedule(
        self,
        mock_post_feed,
        mock_upload_photo,
        mock_parse_md,
        mock_fetch_bytes,
        mock_get_branch,
        mock_parse_repo,
    ):
        mock_fetch_bytes.return_value = self.tweets_md
        mock_parse_md.return_value = (["First post text", "Second post text"], [])
        mock_post_feed.return_value = "fake-post-id"
        mock_upload_photo.return_value = "fake-photo-id"

        result = facebook.launch_social_media_facebook(
            repo_url=self.repo_url,
            article_link=self.article_link,
            page_id="fake-page-id",
            access_token="fake-access-token",
        )

        self.assertEqual(result["post_id"], "fake-post-id")
        self.assertIsNone(result["scheduled_time"])
        mock_post_feed.assert_called_once()
        args, kwargs = mock_post_feed.call_args
        self.assertEqual(args[0], "fake-page-id")
        self.assertEqual(args[1], "fake-access-token")
        self.assertEqual(args[2], ["First post text"])
        self.assertEqual(args[3], self.article_link)
        self.assertIsNone(args[4])
        self.assertIsNone(args[5])

    @patch("jdhapi.utils.facebook.parse_repo_url", return_value=("owner", "repo"))
    @patch("jdhapi.utils.facebook.get_default_branch", return_value="main")
    @patch("jdhapi.utils.facebook.fetch_file_bytes")
    @patch("jdhapi.utils.facebook.parse_tweets_md")
    @patch("jdhapi.utils.facebook.fb_upload_photo")
    @patch("jdhapi.utils.facebook.fb_post_feed")
    def test_launch_with_schedule(
        self,
        mock_post_feed,
        mock_upload_photo,
        mock_parse_md,
        mock_fetch_bytes,
        mock_get_branch,
        mock_parse_repo,
    ):
        mock_fetch_bytes.return_value = self.tweets_md
        mock_parse_md.return_value = (["First post text", "Second post text"], [])
        mock_post_feed.return_value = "fake-post-id"
        mock_upload_photo.return_value = "fake-photo-id"

        schedule_main = datetime.now(timezone.utc) + timedelta(hours=1)

        result = facebook.launch_social_media_facebook(
            repo_url=self.repo_url,
            article_link=self.article_link,
            page_id="fake-page-id",
            access_token="fake-access-token",
            schedule_main=[f"{schedule_main}"],
        )

        self.assertEqual(result["post_id"], "fake-post-id")
        self.assertEqual(result["scheduled_time"], schedule_main)
        mock_post_feed.assert_called_once()
        args, kwargs = mock_post_feed.call_args
        self.assertEqual(args[0], "fake-page-id")
        self.assertEqual(args[1], "fake-access-token")
        self.assertEqual(args[2], ["First post text"])
        self.assertEqual(args[3], self.article_link)
        self.assertIsNone(args[4])
        self.assertEqual(args[5], schedule_main)
