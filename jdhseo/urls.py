from django.urls import path

from . import views

urlpatterns = [
    path('article/<str:pid>/', views.ArticleDetail, name='article-detail'),
    path('issue/<str:pid>/', views.IssueDetail, name='issue-detail'),
    path('article/dg/<str:pid>/', views.ArticleXmlDG, name='article-xml-dg'),
    path('issue/dg/<str:pid>/', views.IssueXmlDG, name='issue-xml-dg'),
    path('package/<str:pid>/', views.Generate_zip, name='generate-zip')
]
