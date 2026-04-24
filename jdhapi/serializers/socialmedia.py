from rest_framework import serializers

from ..models.socialmedia import SocialMedia


class SocialMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = SocialMedia
        fields = [
            "platform",
            "url",
            "scheduled_time",
            "published_time"
        ]
