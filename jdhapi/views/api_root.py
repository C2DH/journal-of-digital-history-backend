from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'authors': reverse('author-list', request=request, format=format),
        'datasets': reverse('dataset-list', request=request, format=format),
        'abstracts': reverse('abstract-list', request=request, format=format),
        'articles': reverse('article-list', request=request, format=format),
        'issues': reverse('issue-list', request=request, format=format),
        'tags': reverse('tag-list', request=request, format=format),
        'callofpapers': reverse('callofpaper-list', request=request, format=format),
    })