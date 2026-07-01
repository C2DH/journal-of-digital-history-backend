from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView

from jdhapi.models import Abstract, Article, CallForPaper, Issue

ARTICLE_STATUSES = [
    ("DRAFT", "Writing"),
    ("TECHNICAL_REVIEW", "Technical review"),
    ("PEER_REVIEW", "Peer review"),
    ("DESIGN_REVIEW", "Design review"),
    ("PUBLISHED", "Published"),
]

ABSTRACT_STATUSES = [
    ("PUBLISHED", "Published"),
    ("ACCEPTED", "Accepted"),
    ("SUBMITTED", "Submitted"),
    ("SUSPENDED", "Suspended"),
    ("ABANDONED", "Abandoned"),
    ("DECLINED", "Declined"),
]


class BarChartDataView(APIView):
    def get(self, request):
        # --- Articles per issue ---
        issues = Issue.objects.all().order_by("pid")

        # Single query: count articles grouped by issue + status
        article_counts = (
            Article.objects.filter(
                issue__in=issues,
                status__in=[s[0] for s in ARTICLE_STATUSES],
            )
            .values("issue_id", "status")
            .annotate(count=Count("abstract_id"))
        )

        # Index counts by (issue_id, status) for fast lookup
        article_count_map = {
            (row["issue_id"], row["status"]): row["count"]
            for row in article_counts
        }

        article_series = []
        for issue in issues:
            obj = {"issueName": issue.name, "pid": issue.pid}
            for status_value, label in ARTICLE_STATUSES:
                obj[label] = article_count_map.get((issue.id, status_value), 0)
            article_series.append(obj)

        article_labels = [issue.pid for issue in issues]

        # --- Advance articles (published but issue not yet published) ---
        advance_count = Article.objects.filter(issue__status='DRAFT', status='PUBLISHED').count()

        advance_series = [
            {
                "issueName": "Advance Articles",
                "pid": "advance",
                "Writing": 0,
                "Technical review": 0,
                "Peer review": 0,
                "Design review": 0,
                "Published": advance_count,
            }
        ]

        # --- Abstracts per call for paper ---
        cfps = CallForPaper.objects.all().order_by("title")

        # Single query: count abstracts grouped by cfp + status
        abstract_counts = (
            Abstract.objects.filter(
                callpaper__in=cfps,
                status__in=[s[0] for s in ABSTRACT_STATUSES],
            )
            .values("callpaper_id", "status")
            .annotate(count=Count("id"))
        )

        abstract_count_map = {
            (row["callpaper_id"], row["status"]): row["count"]
            for row in abstract_counts
        }

        abstract_series = []
        for cfp in cfps:
            obj = {"cfpTitle": cfp.title, "id": cfp.id}
            for status_value, label in ABSTRACT_STATUSES:
                obj[label] = abstract_count_map.get((cfp.id, status_value), 0)
            abstract_series.append(obj)

        abstract_labels = [cfp.title for cfp in cfps]

        print(f"Article series: {article_series}")
        
        return Response(
            {
                "articleSeries": article_series,
                "articleLabels": article_labels,
                "advanceSeries": advance_series,
                "abstractSeries": abstract_series,
                "abstractLabels": abstract_labels,
            }
        )
           