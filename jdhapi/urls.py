from django.urls import path, include
from jdhapi import views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from rest_framework import routers



urlpatterns = [
    path('api/', views.api_root),
    path('api-auth/', include('rest_framework.urls')),
    path('api/authors/', views.AuthorList.as_view(), name='author-list'),
    path('api/authors/<int:pk>/', views.AuthorDetail.as_view(), name='author-detail'),
    path('api/datasets/', views.DatasetList.as_view(), name='dataset-list'),
    path('api/datasets/<int:pk>/', views.DatasetDetail.as_view(), name='dataset-detail'),
    path('api/abstracts/', views.AbstractList.as_view(),name='abstract-list' ),
    path('api/abstracts/<int:pk>/', views.AbstractDetail.as_view(), name='abstract-detail'),
    path('api/submit-abstract/', views.SubmitAbstract)
]
urlpatterns = format_suffix_patterns(urlpatterns)
