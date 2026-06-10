from unittest.mock import Mock, patch

from django.test import TestCase
from jdhapi.models import Abstract, Article, Issue
from jdhapi.utils.ojs import (
    _fetch_submission_and_status,
    assign_substatus,
    find_right_stage_and_round,
    get_active_submission_with_timing,
    get_active_submissions_by_stage,
    get_active_submissions_by_stage_with_details,
    increase_round,
    increase_round_per_stage,
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
        bucket = {"ontime": 0, "delay": 0, "declined": 0, "order": "R1"}

        increase_round(bucket, 10)
        increase_round(bucket, 8)

        self.assertEqual(bucket["delay"], 1)
        self.assertEqual(bucket["ontime"], 1)
        self.assertEqual(bucket["declined"], 0)

    def test_increase_round_per_stage_maps_statuses(self):
        bucket = {
            "assign": 0,
            "awaiting": 0,
            "review": 0,
            "reviewer": 0,
            "revising": 0,
            "order": "R1",
        }

        increase_round_per_stage(bucket, 6)
        increase_round_per_stage(bucket, 7)
        increase_round_per_stage(bucket, 10)
        increase_round_per_stage(bucket, 8)
        increase_round_per_stage(bucket, 100)

        self.assertEqual(bucket["assign"], 1)
        self.assertEqual(bucket["awaiting"], 1)
        self.assertEqual(bucket["review"], 1)
        self.assertEqual(bucket["reviewer"], 1)
        self.assertEqual(bucket["revising"], 1)

    def test_assign_substatus_maps_known_statuses(self):
        review_assignments = [
            {"statusId": 0},
            {"statusId": 5},
            {"statusId": 9},
            {"statusId": 12},
        ]

        result = assign_substatus(review_assignments)

        self.assertEqual(result, ["pending", "accepted", "thanked", "viewed"])

    def test_find_right_stage_and_round_appends_article(self):
        submissions = [{"key": "reviewer-R2", "articles": []}]
        article = {"pid": "pid-001", "title": "Mapped Title"}

        find_right_stage_and_round(submissions, 2, 8, article)

        self.assertEqual(submissions[0]["articles"], [article])

    def test_find_right_stage_and_round_ignores_unmanaged_status(self):
        submissions = [{"key": "reviewer-R2", "articles": []}]
        article = {"pid": "pid-001", "title": "Mapped Title"}

        find_right_stage_and_round(submissions, 2, 999, article)

        self.assertEqual(submissions[0]["articles"], [])

    @patch("jdhapi.utils.ojs.requests.get")
    def test_fetch_submission_and_status_returns_override_for_author_revising(self, mock_get):
        submission_response = Mock()
        submission_response.raise_for_status.return_value = None
        submission_response.json.return_value = {"id": 123}

        decision_response = Mock()
        decision_response.status_code = 200
        decision_response.json.return_value = [{"decision": 4}]

        mock_get.side_effect = [submission_response, decision_response]

        sid, submission, override = _fetch_submission_and_status(123)

        self.assertEqual(sid, 123)
        self.assertEqual(submission, {"id": 123})
        self.assertEqual(override, 100)

    @patch("jdhapi.utils.ojs.requests.get")
    @patch("jdhapi.utils.ojs.get_active_submissions_ids")
    def test_get_active_submission_with_timing_aggregates_rounds(self, mock_ids, mock_get):
        mock_ids.return_value = [1, 2, 3]

        def make_response(round_value, status_id):
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {
                "reviewRounds": [{"round": round_value, "statusId": status_id}]
            }
            return response

        mock_get.side_effect = [
            make_response(1, 8),
            make_response(2, 10),
            make_response(3, 8),
        ]

        result = get_active_submission_with_timing()

        self.assertEqual(result[0], {"ontime": 1, "delay": 0, "declined": 0, "order": "R1"})
        self.assertEqual(result[1], {"ontime": 0, "delay": 1, "declined": 0, "order": "R2"})
        self.assertEqual(result[2], {"ontime": 1, "delay": 0, "declined": 0, "order": "R3+"})

    @patch("jdhapi.utils.ojs.is_author_revising")
    @patch("jdhapi.utils.ojs.requests.get")
    @patch("jdhapi.utils.ojs.get_active_submissions_ids")
    def test_get_active_submissions_by_stage_aggregates_counts(self, mock_ids, mock_get, mock_revising):
        mock_ids.return_value = [1, 2, 3]
        mock_revising.side_effect = [6, 100, 10]

        def make_response(round_value, status_id):
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {
                "reviewRounds": [{"round": round_value, "statusId": status_id}]
            }
            return response

        mock_get.side_effect = [
            make_response(1, 6),
            make_response(2, 1),
            make_response(3, 10),
        ]

        result = get_active_submissions_by_stage()

        self.assertEqual(result[0]["assign"], 1)
        self.assertEqual(result[1]["revising"], 1)
        self.assertEqual(result[2]["review"], 1)

    @patch("jdhapi.utils.ojs._fetch_submission_and_status")
    @patch("jdhapi.utils.ojs.get_active_submissions_ids")
    def test_get_active_submissions_by_stage_with_details_maps_articles(self, mock_ids, mock_fetch):
        mock_ids.return_value = [123]
        mock_fetch.return_value = (
            123,
            {
                "id": 123,
                "publications": [{"fullTitle": {"en": "Mapped Title"}, "authorsString": "Jane Doe"}],
                "reviewAssignments": [{"statusId": 9}],
                "reviewRounds": [{"round": 1, "statusId": 6}],
                "urlWorkflow": "https://ojs/workflow/123",
            },
            None,
        )

        result = get_active_submissions_by_stage_with_details()

        assign_r1 = next(entry for entry in result if entry["key"] == "assign-R1")
        self.assertEqual(len(assign_r1["articles"]), 1)
        self.assertEqual(assign_r1["articles"][0]["pid"], "pid-001")
        self.assertEqual(assign_r1["articles"][0]["substatus"], ["thanked"])