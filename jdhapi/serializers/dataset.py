from jdhapi.serializers.abstract import AbstractSerializer
from rest_framework import serializers
from ..models.dataset import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    abstracts = AbstractSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ['id', 'url', 'description', 'abstracts']


class DatasetSlimSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dataset
        fields = ['id', 'url', 'description']
