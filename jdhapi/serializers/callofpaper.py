from rest_framework import serializers
from ..models.callofpaper import CallOfPaper


class CallOfPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallOfPaper
        fields = "__all__"
