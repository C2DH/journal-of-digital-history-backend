from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/fingerprint/<int:pk>/", views.fingerprint, name="fingerprint"),
    path(
        "dashboard/promotion/bluesky",
        views.bluesky_campaign,
        name="bluesky-campaign",
    ),
    path(
        "dashboard/promotion/facebook",
        views.facebook_campaign,
        name="facebook-campaign",
    ),
]
