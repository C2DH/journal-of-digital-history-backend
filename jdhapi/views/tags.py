from jdhapi.models import Tag
from jdhapi.serializers.tag import TagSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics


class TagList(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "category", "name"]


class TagDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
