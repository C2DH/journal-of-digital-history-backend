from jdhapi.models import Article, Issue, Abstract
from jdhapi.serializers.article import ArticleSerializer
from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import generics, filters
from jdhapi.serializers.issue import IssueSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404


class IssueList(generics.ListCreateAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        "id",
        "pid",
        "name",
        "description",
        "creation_date",
        "publication_date",
        "cover_date",
        "status",
        "volume",
        "issue",
        "is_open_ended",
    ]
    ordering_fields = [
        "creation_date",
        "publication_date",
        "pid",
    ]


class IssueDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Issue.objects.all()
    serializer_class = IssueSerializer
    lookup_field = "pid"


class IssueArticlesList(generics.ListAPIView):
    serializer_class = ArticleSerializer

    def get_queryset(self):
        pid = self.kwargs["pid"]
        issue = get_object_or_404(Issue, pid=pid)
        return Article.objects.filter(issue=issue)
    
    
    
class IssueAbstractsList(generics.ListAPIView):
    serializer_class = AbstractSerializer
    
    def get_queryset(self):
        pid =self.kwargs["pid"]
        issue = get_object_or_404(Issue, pid=pid)
        articles = Article.objects.filter(issue=issue)
        abstract_pids = articles.values_list("abstract__pid", flat=True)
        return Abstract.objects.filter(pid__in=abstract_pids)
    