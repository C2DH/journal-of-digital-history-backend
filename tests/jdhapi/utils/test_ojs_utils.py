from unittest.mock import Mock, patch

import requests
from django.test import TestCase

from jdhapi.models import Abstract, Article, Issue
from jdhapi.utils.ojs import (
    fetch_submission_and_status,
    find_right_stage_and_round,
    get_active_submission_with_timing,
    get_active_submissions_by_stage_with_details,
    increase_round,
)


class OJSUtilsTestCase(TestCase):
    def setUp(self):
        self.issue = Issue.objects.create(
            id=10,
            pid="jdh010",
            name="Issue 10",
            volume=1,
            issue=10,
            status=Issue.Status.PUBLISHED,
        )
        self.abstract = Abstract.objects.create(
            pid="pid-001",
            title="Mapped Title",
            abstract="Body",
            contact_email="a@test.com",
            contact_lastname="Doe",
        )
        self.article = Article.objects.create(
            abstract=self.abstract,
            data={"title": "Mapped Title"},
            issue=self.issue,
            ojs_submission_id=123,
        )

    def test_increase_round_counts_delay_only_for_status_10(self):
        bucket = {"submitted": 0, "ontime": 0, "delay": 0, "declined": 0, "order": "R1"}

        increase_round(bucket, 10, 1)
        increase_round(bucket, 8, 0)

        self.assertEqual(bucket["submitted"], 1)
        self.assertEqual(bucket["delay"], 1)
        self.assertEqual(bucket["ontime"], 1)
        self.assertEqual(bucket["declined"], 0)

    def test_find_right_stage_and_round_maps_submitted_ontime_delay_declined(self):
        submitted_bucket = {"key": "submitted-R1", "articles": []}
        ontime_bucket = {"key": "ontime-R2", "articles": []}
        delay_bucket = {"key": "delay-R2", "articles": []}
        declined_bucket = {"key": "declined-R3", "articles": []}
        submissions = [submitted_bucket, ontime_bucket, delay_bucket, declined_bucket]

        find_right_stage_and_round(submissions, 1, 0, 3, {"pid": "a"})
        find_right_stage_and_round(submissions, 2, 8, 3, {"pid": "b"})
        find_right_stage_and_round(submissions, 2, 10, 3, {"pid": "c"})
        find_right_stage_and_round(submissions, 3, 5, 3, {"pid": "d"})

        self.assertEqual(submitted_bucket["articles"], [{"pid": "a"}])
        self.assertEqual(ontime_bucket["articles"], [{"pid": "b"}])
        self.assertEqual(delay_bucket["articles"], [{"pid": "c"}])
        self.assertEqual(declined_bucket["articles"], [{"pid": "d"}])

    def test_find_right_stage_and_round_maps_stage_1_and_stage_4(self):
        submitted_bucket = {"key": "submitted-R1", "articles": []}
        over_bucket = {"key": "over-R3", "articles": []}
        submissions = [submitted_bucket, over_bucket]

        find_right_stage_and_round(submissions, 1, 0, 1, {"pid": "a"})
        find_right_stage_and_round(submissions, 3, 0, 4, {"pid": "b"})

        self.assertEqual(submitted_bucket["articles"], [{"pid": "a"}])
        self.assertEqual(over_bucket["articles"], [{"pid": "b"}])

    def test_find_right_stage_and_round_logs_when_key_missing(self):
        submissions = [{"key": "submitted-R1", "articles": []}]

        find_right_stage_and_round(submissions, 2, 0, 3, {"pid": "a"})

        self.assertEqual(submissions[0]["articles"], [])

    @patch("jdhapi.utils.ojs.requests.get")
    def test_fetch_submission_and_status_returns_submission_on_success(self, mock_get):
        mock_get.return_value = Mock(
            raise_for_status=Mock(return_value=None),
            json=lambda: {"id": 123, "reviewRounds": []},
        )

        sid, submission = fetch_submission_and_status(123)

        self.assertEqual(sid, 123)
        self.assertEqual(submission, {"id": 123, "reviewRounds": []})

    @patch("jdhapi.utils.ojs.requests.get")
    def test_fetch_submission_and_status_on_request_failure(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("boom")

        result = fetch_submission_and_status(123)

        self.assertEqual(result, (123, None))

    @patch("jdhapi.utils.ojs.get_submissions_copyediting_counter")
    @patch("jdhapi.utils.ojs.fetch_submission")
    @patch("jdhapi.utils.ojs.get_submissions_submitted_counter")
    @patch("jdhapi.utils.ojs.get_submissions_peer_review_ids")
    def test_get_active_submission_with_timing_aggregates_rounds(
        self, mock_ids, mock_count, mock_fetch, mock_copyediting_counter
    ):
        mock_ids.return_value = [1, 2, 3]
        mock_count.return_value = 0
        responses = {
            1: {"reviewRounds": [{"round": 1, "statusId": 8}]},
            2: {"reviewRounds": [{"round": 2, "statusId": 10}]},
            3: {"reviewRounds": [{"round": 3, "statusId": 8}]},
        }
        mock_fetch.side_effect = lambda sid: (sid, responses[sid])

        result = get_active_submission_with_timing()

        self.assertEqual(
            result[0], {"submitted": 0, "ontime": 1, "delay": 0, "declined": 0, "over": 0, "order": "R1"}
        )
        self.assertEqual(
            result[1], {"submitted": 0, "ontime": 0, "delay": 1, "declined": 0, "over": 0, "order": "R2"}
        )
        self.assertEqual(
            result[2], {"submitted": 0, "ontime": 1, "delay": 0, "declined": 0, "over": 0, "order": "R3+"}
        )

    @patch("jdhapi.utils.ojs.get_submissions_copyediting")
    @patch("jdhapi.utils.ojs.get_submissions")
    @patch("jdhapi.utils.ojs.fetch_submission_and_status")
    @patch("jdhapi.utils.ojs.get_submissions_peer_review_ids")
    def test_get_active_submissions_by_stage_with_details_maps_peer_review_article(
        self, mock_ids, mock_fetch, mock_stage1, mock_stage4
    ):
        mock_ids.return_value = [123]
        mock_stage4.return_value = []
        mock_fetch.return_value = (
            123,
            {
                "id": 123,
                "publications": [
                    {"fullTitle": {"en": "Mapped Title"}, "authorsString": "Jane Doe"}
                ],
                "reviewRounds": [{"round": 1, "statusId": 8, "status": "In review"}],
                "urlWorkflow": "https://ojs/workflow/123",
            },
        )
        mock_stage1.return_value = []

        result = get_active_submissions_by_stage_with_details()

        ontime_r1 = next(entry for entry in result if entry["key"] == "ontime-R1")
        self.assertEqual(len(ontime_r1["articles"]), 1)
        self.assertEqual(ontime_r1["articles"][0]["pid"], "pid-001")
        self.assertEqual(ontime_r1["articles"][0]["authors"], "Jane Doe")
        self.assertEqual(ontime_r1["articles"][0]["url"], "https://ojs/workflow/123")

    @patch("jdhapi.utils.ojs.get_submissions_copyediting")
    @patch("jdhapi.utils.ojs.get_submissions")
    @patch("jdhapi.utils.ojs.fetch_submission_and_status")
    @patch("jdhapi.utils.ojs.get_submissions_peer_review_ids")
    def test_get_active_submissions_by_stage_with_details_includes_stage_1_submissions(
        self, mock_ids, mock_fetch, mock_stage1, mock_stage4
    ):
        mock_ids.return_value = []
        mock_stage4.return_value = []
        mock_stage1.return_value = [
            {
                "ojs_submission_id": 123,
                "ojs_workflow_url": "https://ojs/workflow/123",
                "title": "Mapped Title",
                "author": "Jane Doe",
                "stage_id": 1,
            }
        ]

        result = get_active_submissions_by_stage_with_details()

        submitted_r1 = next(entry for entry in result if entry["key"] == "submitted-R1")
        self.assertEqual(len(submitted_r1["articles"]), 1)
        self.assertEqual(submitted_r1["articles"][0]["pid"], "pid-001")

    @patch("jdhapi.utils.ojs.get_submissions_copyediting")
    @patch("jdhapi.utils.ojs.get_submissions")
    @patch("jdhapi.utils.ojs.fetch_submission_and_status")
    @patch("jdhapi.utils.ojs.get_submissions_peer_review_ids")
    def test_get_active_submissions_by_stage_with_details_includes_stage_4_submissions(
        self, mock_ids, mock_fetch, mock_stage1, mock_stage4
    ):
        mock_ids.return_value = []
        mock_stage1.return_value = []
        mock_stage4.return_value = [
            {
                "ojs_submission_id": 123,
                "ojs_workflow_url": "https://ojs/workflow/123",
                "title": "Mapped Title",
                "author": "Jane Doe",
                "stage_id": 4,
            }
        ]

        result = get_active_submissions_by_stage_with_details()

        over_r3 = next(entry for entry in result if entry["key"] == "over-R3")
        self.assertEqual(len(over_r3["articles"]), 1)
        self.assertEqual(over_r3["articles"][0]["pid"], "pid-001")
        self.assertEqual(over_r3["articles"][0]["title"], "Mapped Title")

    @patch("jdhapi.utils.ojs.get_submissions_copyediting")
    @patch("jdhapi.utils.ojs.get_submissions")
    @patch("jdhapi.utils.ojs.fetch_submission_and_status")
    @patch("jdhapi.utils.ojs.get_submissions_peer_review_ids")
    def test_get_active_submissions_by_stage_with_details_accepts_dict_title_in_stage_1(
        self, mock_ids, mock_fetch, mock_stage1, mock_stage4
    ):
        mock_ids.return_value = []
        mock_stage4.return_value = []
        mock_stage1.return_value = [
            {
                "ojs_submission_id": 123,
                "ojs_workflow_url": "https://ojs/workflow/123",
                "title": {"en": "Mapped Title"},
                "author": "Jane Doe",
                "stage_id": 1,
            }
        ]

        result = get_active_submissions_by_stage_with_details()

        submitted_r1 = next(entry for entry in result if entry["key"] == "submitted-R1")
        self.assertEqual(len(submitted_r1["articles"]), 1)
        self.assertEqual(submitted_r1["articles"][0]["title"], "Mapped Title")

    @patch("jdhapi.utils.ojs.get_submissions_copyediting")
    @patch("jdhapi.utils.ojs.get_submissions")
    @patch("jdhapi.utils.ojs.fetch_submission_and_status")
    @patch("jdhapi.utils.ojs.get_submissions_peer_review_ids")
    def test_get_active_submissions_by_stage_with_details_no_match_has_null_pid(
        self, mock_ids, mock_fetch, mock_stage1, mock_stage4
    ):
        mock_ids.return_value = [999]
        mock_stage4.return_value = []
        mock_fetch.return_value = (
            999,
            {
                "id": 999,
                "publications": [
                    {"fullTitle": {"en": "Unknown Title"}, "authorsString": "No author"}
                ],
                "reviewRounds": [{"round": 1, "statusId": 5}],
                "urlWorkflow": "https://ojs/workflow/999",
            },
        )
        mock_stage1.return_value = []

        result = get_active_submissions_by_stage_with_details()

        declined_r1 = next(entry for entry in result if entry["key"] == "declined-R1")
        self.assertEqual(declined_r1["articles"][0]["pid"], None)
