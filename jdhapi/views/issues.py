from jdhapi.models import Issue
from rest_framework import generics, filters
from jdhapi.serializers.issue import IssueSerializer
from django_filters.rest_framework import DjangoFilterBackend


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
