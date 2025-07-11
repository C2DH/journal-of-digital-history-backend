from django_filters.rest_framework import DjangoFilterBackend
from jdhapi.models import Role, Issue
from jdhapi.serializers.role import RoleSerializer
from rest_framework import generics


class RoleList(generics.ListCreateAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "order_id", "author", "article"]


class RoleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Issue.objects.all()
    serializer_class = RoleSerializer
