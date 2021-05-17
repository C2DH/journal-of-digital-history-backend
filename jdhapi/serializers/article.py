from rest_framework import serializers
from ..models.article import Article
from .tag import TagSerializer
from .issue import IssueSerializer
from .author import AuthorSerializer


class ArticleSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    issue = IssueSerializer()
    authors = AuthorSerializer(many=True)

    class Meta:
        model = Article
        fields = ["abstract", "repository_url", "status", "repository_type", "notebook_url", "notebook_commit_hash", "data", "tags", "issue", "authors"]
