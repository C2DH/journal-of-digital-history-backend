from django.urls import path

from . import views

urlpatterns = [
    path('article/<str:pid>/', views.article_detail, name='article-detail'),
    path('issue/<str:pid>/', views.issue_detail, name='issue-detail'),
    path('article/dg/<str:pid>/', views.article_xml_dg_view, name='article-xml-dg'),
    path('issue/dg/<str:pid>/', views.issue_xml_dg_view, name='issue-xml-dg'),
    path('package/<str:pid>/', views.generate_zip, name='generate-zip')
]
