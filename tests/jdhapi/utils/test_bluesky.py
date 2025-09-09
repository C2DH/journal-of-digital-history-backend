import json
import unittest
from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from jdhapi.utils import bluesky


class TestBlueskyLaunch(unittest.TestCase):
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

    @patch("jdhapi.utils.bluesky.time.sleep", return_value=None)
    @patch("jdhapi.utils.bluesky.get_default_branch", return_value="main")
    @patch("jdhapi.utils.bluesky.file_exists", return_value=True)
    @patch("jdhapi.utils.bluesky.fetch_file_bytes")
    @patch("jdhapi.utils.bluesky.Client")
    def test_launch_without_schedule(
        self,
        mock_client_cls,
        mock_fetch_bytes,
        mock_file_exists,
        mock_get_branch,
        mock_sleep,
    ):

        mock_fetch_bytes.return_value = self.tweets_md

        # Create a fake client
        client_inst = Mock()
        client_inst.me = SimpleNamespace(did="did:example")

        create_record_mock = Mock(
            side_effect=[
                SimpleNamespace(uri="uri-main", cid="cid-main"),
                SimpleNamespace(uri="uri-reply-1", cid="cid-reply-1"),
                SimpleNamespace(uri="uri-reply-2", cid="cid-reply-2"),
            ]
        )

        repo_ns = SimpleNamespace(create_record=create_record_mock)
        atproto_ns = SimpleNamespace(repo=repo_ns)
        client_inst.com = SimpleNamespace(atproto=atproto_ns)

        client_inst.upload_blob = Mock(
            return_value=SimpleNamespace(
                blob={
                    "cid": "fake-blob-id",
                    "mimeType": "image/png",
                    "size": 12345,
                    "ref": "https://example.com/og-image.png",
                }
            )
        )

        mock_client_cls.return_value = client_inst

        article_html = (
            "<html><head>"
            '<meta property="og:title" content="Example Title" />'
            '<meta property="og:description" content="Example Description" />'
            '<meta property="og:image" content="https://example.com/og-image.png" />'
            "</head><body>...</body></html>"
        )
        mock_html_resp = Mock(
            status_code=200, text=article_html, headers={"Content-Type": "text/html"}
        )
        mock_img_resp = Mock(
            status_code=200,
            content=b"\x89PNG\r\n\x1a\n...",
            headers={"Content-Type": "image/png"},
        )

        def requests_get_side_effect(url, *args, **kwargs):
            if url.startswith("https://example.com/og-image.png"):
                return mock_img_resp
            if url.startswith("https://example.com/article"):
                return mock_html_resp

            return Mock(status_code=404, text="not found")

        with patch(
            "jdhapi.utils.bluesky.requests.get", side_effect=requests_get_side_effect
        ):
            result = bluesky.launch_social_media_bluesky(
                repo_url=self.repo_url,
                branch="",
                article_link=self.article_link,
                login="user",
                password="pass",
                schedule_main="",
            )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["total_posts"], 3)
        self.assertEqual(result["scheduled_jobs"], 0)
        self.assertEqual(create_record_mock.call_count, 3)

    @patch("jdhapi.utils.bluesky.time.sleep", return_value=None)
    @patch("jdhapi.utils.bluesky.get_default_branch", return_value="main")
    @patch("jdhapi.utils.bluesky.file_exists", return_value=True)
    @patch("jdhapi.utils.bluesky.fetch_file_bytes")
    @patch("jdhapi.utils.bluesky.Client")
    def test_launch_with_schedule(
        self,
        mock_client_cls,
        mock_fetch_bytes,
        mock_file_exists,
        mock_get_default_branch,
        mock_sleep,
    ):
        mock_fetch_bytes.return_value = self.tweets_md

        # Mock client
        client_inst = Mock()
        client_inst.me = SimpleNamespace(did="did:example")
        # create_record may not be invoked if all times are in the future
        client_inst.com = SimpleNamespace(
            atproto=SimpleNamespace(repo=SimpleNamespace(create_record=Mock()))
        )
        client_inst.upload_blob = Mock(
            return_value=SimpleNamespace(
                blob={
                    "cid": "fake-blob-id",
                    "mimeType": "image/png",
                    "size": 12345,
                    "ref": "https://example.com/og-image.png",
                }
            )
        )

        mock_client_cls.return_value = client_inst

        # Prepare schedule
        now = datetime.now(timezone.utc)
        times = [
            (now + timedelta(minutes=20)).isoformat(),
            (now + timedelta(minutes=25)).isoformat(),
            (now + timedelta(minutes=30)).isoformat(),
        ]
        schedule_json = json.dumps(times)
        mock_scheduler = Mock()
        added_jobs = []

        def fake_add_job(func, trigger, run_date, args=None):
            job = SimpleNamespace(
                func=func, trigger=trigger, run_date=run_date, args=args
            )
            added_jobs.append(job)
            return job

        mock_scheduler.add_job.side_effect = fake_add_job
        mock_scheduler.add_listener.return_value = None

        with patch(
            "jdhapi.utils.bluesky._get_background_scheduler",
            return_value=mock_scheduler,
        ):
            # Act
            result = bluesky.launch_social_media_bluesky(
                repo_url=self.repo_url,
                branch="",
                article_link=self.article_link,
                login="user",
                password="pass",
                schedule_main=schedule_json,
            )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["total_posts"], 3)
        self.assertEqual(result["scheduled_jobs"], 3)
        self.assertEqual(len(added_jobs), 3)
        for job in added_jobs:
            self.assertTrue(hasattr(job, "run_date"))
            self.assertGreater(job.run_date, now)


if __name__ == "__main__":
    unittest.main()
