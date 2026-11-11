from rest_framework import serializers

from jdhapi.serializers.abstract import AbstractSerializer

from ..models.article import Article
from .author import AuthorSlimSerializer
from .issue import IssueSerializer
from .socialmedia import SocialMediaSerializer
from .tag import TagSerializer


class ArticleSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    issue = IssueSerializer()
    abstract = AbstractSerializer()
    authors = AuthorSlimSerializer(many=True)
    campaigns = SocialMediaSerializer(many=True)

    kernel_language = serializers.SerializerMethodField()
    status_log = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "abstract",
            "repository_url",
            "github_issue",
            "status",
            "publication_date",
            "repository_type",
            "copyright_type",
            "notebook_url",
            "notebook_commit_hash",
            "notebook_path",
            "binder_url",
            "doi",
            "dataverse_url",
            "data",
            "citation",
            "kernel_language",
            "tags",
            "issue",
            "authors",
            "ojs_submission_id",
            "campaigns",
            "fingerprint",
            "status_log"
        ]
    
    def get_kernel_language(self, obj):
        return obj.get_kernel_language()

    def get_status_log(self, obj):
        status_changes = []

        for record in obj.history.all():
            status_changes.append(
                {
                    "date": record.history_date,
                    "user": record.history_user.username,
                    "status": record.status,
                }
            )
        return status_changes