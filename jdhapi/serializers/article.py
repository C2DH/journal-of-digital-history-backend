from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import serializers
from ..models.article import Article
from .tag import TagSerializer
from .issue import IssueSerializer
from .author import AuthorSlimSerializer


class ArticleSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    issue = IssueSerializer()
    authors = AuthorSlimSerializer(many=True)

    class Meta:
        model = Article
        fields = ["abstract", "repository_url", "status", "repository_type", "notebook_url", "notebook_commit_hash", "data", "tags", "issue", "authors"]
