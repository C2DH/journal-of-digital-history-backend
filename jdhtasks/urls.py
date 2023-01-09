from django.urls import re_path
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
  re_path(r'^webhook/(?P<username>\w+)/(?P<repo>\w+)/$', views.webhook),
]

urlpatterns = format_suffix_patterns(urlpatterns)