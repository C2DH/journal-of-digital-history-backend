from django_filters.rest_framework import DjangoFilterBackend
from jdhapi.models import Dataset
from jdhapi.serializers.dataset import DatasetSlimSerializer
from rest_framework import generics


class DatasetList(generics.ListCreateAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSlimSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "url", "description"]


class DatasetDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dataset.objects.all()
    serializer_class = DatasetSlimSerializer
