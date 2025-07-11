from datetime import date
from django_filters.rest_framework import DjangoFilterBackend
from jdhapi.serializers.callforpaper import CallForPaperSerializer
from jdhapi.models import CallForPaper
from rest_framework import generics


class CallForPaperList(generics.ListCreateAPIView):
    queryset = CallForPaper.objects.all()
    serializer_class = CallForPaperSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "id",
        "deadline_abstract",
        "deadline_article",
        "title",
        "folder_name",
    ]


class CallForPaperListOpen(generics.ListCreateAPIView):
    queryset = CallForPaper.objects.filter(deadline_abstract__gte=date.today())
    serializer_class = CallForPaperSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "id",
        "deadline_abstract",
        "deadline_article",
        "title",
        "folder_name",
    ]


class CallForPaperDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CallForPaper.objects.all()
    serializer_class = CallForPaperSerializer
    ordering_fields = ["deadline_abstract", "deadline_article"]
    lookup_field = "folder_name"
