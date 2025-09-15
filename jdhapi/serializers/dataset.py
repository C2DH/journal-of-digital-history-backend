from jdhapi.serializers.abstract import AbstractSlimSerializer
from rest_framework import serializers
from ..models.dataset import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    abstracts = AbstractSlimSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ["id", "url", "description", "abstracts"]


class DatasetSlimSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dataset
        fields = ("id", "url", "description")
