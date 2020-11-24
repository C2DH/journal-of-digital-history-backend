from django.urls import path
from . import views


urlpatterns = [
    path('',views.home, name='home'),
    path('sendmail', views.sendmail, name='sendmail'),
    path('abstract/<int:pk>/', views.abstract, name='abstract'),
    path('accepted/<int:pk>/', views.accepted, name='accepted'),
    path('declined/<int:pk>/', views.declined, name='declined'),
] 
