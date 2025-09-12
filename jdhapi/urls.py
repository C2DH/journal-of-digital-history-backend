from django.urls import path, include
from jdhapi import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path("api/", views.api_root),
    path("api/me", views.api_me, name="me"),
    path("api-auth/", include("rest_framework.urls")),
    path("api/abstracts/", views.AbstractList.as_view(), name="abstract-list"),
    path(
        "api/abstracts/<str:pid>/",
        views.AbstractDetail.as_view(),
        name="abstract-detail",
    ),
    path(
        "api/abstracts/status",
        views.update_abstract_status,
        name="abstract-change-status",
    ),
    path(
        "api/abstracts/<str:pid>/status",
        views.update_abstract_status_with_email,
        name="abstract-change-status-with-email",
    ),
    path("api/abstracts/submit", views.submit_abstract, name="submit-abstract"),
    path("api/articles/", views.ArticleList.as_view(), name="article-list"),
    path(
        "api/articles/status",
        views.update_article_status,
        name="article-change-status",
    ),
    path(
        "api/articles/<str:abstract__pid>/",
        views.ArticleDetail.as_view(),
        name="article-detail",
    ),
    path(
        "api/articles/bluesky",
        views.bluesky_campaign,
        name="articles-bluesky",
    ),
    path(
        "api/articles/facebook",
        views.facebook_campaign,
        name="articles-facebook",
    ),
    path("api/authors/", views.AuthorList.as_view(), name="author-list"),
    path("api/authors/<int:pk>/", views.AuthorDetail.as_view(), name="author-detail"),
    path(
        "api/callforpaper/", views.CallForPaperList.as_view(), name="callforpaper-list"
    ),
    path(
        "api/callforpaper/open",
        views.CallForPaperListOpen.as_view(),
        name="callforpaper-list",
    ),
    path(
        "api/callforpaper/<str:folder_name>/",
        views.CallForPaperDetail.as_view(),
        name="callforpaper-detail",
    ),
    path(
        "api/check-github-id/<str:username>",
        views.check_github_id,
        name="check-github-id",
    ),
    path("api/csrf/", views.get_csrf, name="get_csrf"),
    path("api/datasets/", views.DatasetList.as_view(), name="dataset-list"),
    path(
        "api/datasets/<int:pk>/", views.DatasetDetail.as_view(), name="dataset-detail"
    ),
    path("api/generate-notebook/<str:pid>", views.generate_notebook),
    path("api/issues/", views.IssueList.as_view(), name="issue-list"),
    path("api/issues/<str:pid>/", views.IssueDetail.as_view(), name="issue-detail"),
    path("api/login/", views.CustomLoginView.as_view(), name="custom-login"),
    path("api/logout/", views.custom_logout, name="custom_logout"),
    path("api/tags/", views.TagList.as_view(), name="tag-list"),
    path("api/tags/<int:pk>/", views.TagDetail.as_view(), name="tag-detail"),
]
urlpatterns = format_suffix_patterns(urlpatterns)
