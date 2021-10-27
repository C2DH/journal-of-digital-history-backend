from django.urls import path

from . import views

urlpatterns = [
    path('article/<str:pid>/', views.ArticleDetail, name='article-detail'),
    path('issue/<str:pid>/', views.IssueDetail, name='issue-detail'),
]
