from jdhapi.serializers.author import AuthorSlimSerializer
from jdhapi.serializers.article import ArticleSerializer
from rest_framework import serializers
from ..models.role import Role


class RoleSerializer(serializers.ModelSerializer):
    author = AuthorSlimSerializer()
    article = ArticleSerializer()

    class Meta:
        model = Role
        fields = ['id', 'order_id', 'author', 'article']
