from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "authors": reverse("author-list", request=request, format=format),
            "authors-detail": reverse("author-detail", args=[1], request=request, format=format),
            "datasets": reverse("dataset-list", request=request, format=format),
            "dataset-detail": reverse("dataset-detail", args=[1], request=request, format=format),
            "abstracts": reverse("abstract-list", request=request, format=format),
            "abstract-detail": reverse("abstract-detail", args=["example-pid"], request=request, format=format),
            "articles": reverse("article-list", request=request, format=format),
            "article-detail": reverse("article-detail", args=["example-pid"], request=request, format=format),
            "issues": reverse("issue-list", request=request, format=format),
            "issue-detail": reverse("issue-detail", args=["example-pid"], request=request, format=format),
            "issue-articles": reverse("issue-articles-list", args=["example-pid"], request=request, format=format),
            "issue-abstracts": reverse("issue-abstracts-list", args=["example-pid"], request=request, format=format),
            "callforpapers": reverse("callforpaper-list", request=request, format=format),
            "callforpapers-open": reverse("callforpaper-list", request=request, format=format),
            "callforpaper-detail": reverse("callforpaper-detail", args=["example-folder"], request=request, format=format),
            "check-github-id": reverse("check-github-id", args=["example-username"], request=request, format=format),
            "get_csrf": reverse("get_csrf", request=request, format=format),
            "login": reverse("custom-login", request=request, format=format),
            "logout": reverse("custom_logout", request=request, format=format),
            "tags": reverse("tag-list", request=request, format=format),
            "tag-detail": reverse("tag-detail", args=[1], request=request, format=format),
        }
    )