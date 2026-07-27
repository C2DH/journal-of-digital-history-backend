from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "authors": reverse("author-list", request=request, format=format),
            "authors-detail": reverse("author-list", request=request, format=format) + "{id}/",
            "abstracts": reverse("abstract-list", request=request, format=format),
            "abstract-detail": reverse("abstract-list", request=request, format=format) + "{pid}/",
            "articles": reverse("article-list", request=request, format=format),
            "article-detail": reverse("article-list", request=request, format=format) + "{pid}/",
            "article-status": reverse("article-list", request=request, format=format) + "{pid}/status/",
            "datasets": reverse("dataset-list", request=request, format=format),
            "dataset-detail": reverse("dataset-list", request=request, format=format) + "{id}/",
            "issues": reverse("issue-list", request=request, format=format),
            "issue-detail": reverse("issue-list", request=request, format=format) + "{pid}/",
            "issue-articles": reverse("issue-list", request=request, format=format) + "{pid}/articles/",
            "issue-abstracts": reverse("issue-list", request=request, format=format) + "{pid}/abstracts/",
            "callforpapers": reverse("callforpaper-list", request=request, format=format),
            "callforpapers-open": reverse("callforpaper-list", request=request, format=format),
            "callforpaper-detail": reverse("callforpaper-list", request=request, format=format) + "/{folder}/",
            "tags": reverse("tag-list", request=request, format=format),
            "tag-detail": reverse("tag-list", request=request, format=format) + "{id}/",
            "check-github-id": reverse("check-github-id", args=["example-username"], request=request, format=format).replace("example-username", "{username}"),
            "login": reverse("custom-login", request=request, format=format),
            "logout": reverse("custom_logout", request=request, format=format),
        }
    )