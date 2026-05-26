from django.db import models


class SocialMedia(models.Model):

    class Platform(models.TextChoices):
        FACEBOOK = "FACEBOOK", "Facebook"
        BLUESKY = "BLUESKY", "Bluesky"

    article = models.ForeignKey("jdhapi.Article", on_delete=models.CASCADE, related_name="campaigns")
    platform = models.CharField(max_length=20, choices=Platform.choices)
    url = models.URLField(max_length=254, null=True, blank=True)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    published_time = models.DateTimeField(blank=True, null=True)