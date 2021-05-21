from django.urls import path
from . import views


urlpatterns = [
    path('dashboard', views.home, name='dashboard'),
    path('dashboard/abstractSubmissions', views.abstractSubmissions, name='abstractSubmissions'),
    path('dashboard/abstract/<int:pk>/', views.abstract, name='abstract'),
    path('dashboard/accepted/<int:pk>/', views.accepted, name='accepted'),
    path('dashboard/declined/<int:pk>/', views.declined, name='declined'),
    path('dashboard/abandoned/<int:pk>/', views.abandoned, name='abandoned')
]
