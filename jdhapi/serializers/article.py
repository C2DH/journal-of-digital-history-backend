from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import serializers
from ..models.article import Article
from .tag import TagSerializer
from .issue import IssueSerializer
from .author import AuthorSlimSerializer


class ArticleSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    issue = IssueSerializer()
    abstract = AbstractSerializer()
    authors = AuthorSlimSerializer(many=True)
    # abstract = serializers.SlugRelatedField(
    #    read_only=True,
    #    slug_field='pid',
    # )

    kernel_language = serializers.SerializerMethodField()

    def get_kernel_language(self, obj):
        return obj.get_kernel_language()

    class Meta:
        model = Article
        fields = [
            "abstract", "repository_url", "status", "publication_date", "repository_type",
            "copyright_type", "notebook_url", "notebook_commit_hash", "notebook_path",
            "binder_url", "doi", "dataverse_url", "data", "citation", "kernel_language",
            "tags", "issue", "authors", "fingerprint"
        ]
