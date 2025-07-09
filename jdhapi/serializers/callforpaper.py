from rest_framework import serializers
from ..models.callforpaper import CallForPaper


class CallForPaperSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallForPaper
        fields = "__all__"
