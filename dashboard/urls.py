from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/fingerprint/<int:pk>/", views.fingerprint, name="fingerprint"),
]
