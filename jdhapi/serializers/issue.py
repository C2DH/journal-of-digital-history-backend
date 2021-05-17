from rest_framework import serializers
from ..models.issue import Issue


class IssueSerializer(serializers.ModelSerializer):

    class Meta:
        model = Issue
        fields = ["id", "name", "description", "creation_date", "publication_date", "data"]
