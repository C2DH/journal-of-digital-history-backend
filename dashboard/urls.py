from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/fingerprint/<int:pk>/", views.fingerprint, name="fingerprint"),
    path(
        "dashboard/socialmedia/promotion",
        views.launching_social_media_campaign,
        name="launching-social-media-campaign",
    ),
]
