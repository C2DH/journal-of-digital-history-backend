from rest_framework import serializers
from ..models.issue import Issue


class IssueSerializer(serializers.ModelSerializer):

    class Meta:
        model = Issue
        fields = ["id", "pid", "name", "description", "creation_date", "publication_date", "cover_date", "status", "data", "volume", "issue","is_open_ended"]
