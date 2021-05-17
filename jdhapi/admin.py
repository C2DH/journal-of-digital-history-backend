import os
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Author, Abstract, Dataset, Article, Issue, Tag, Role

# Register your models here.
admin.site.register(Abstract)
admin.site.register(Dataset)
admin.site.register(Author)
admin.site.register(Article)
admin.site.register(Issue)
admin.site.register(Tag)
admin.site.register(Role)

admin.site.site_url = "/dashboard"

admin.site.site_header = mark_safe(
    '<b style="color:white">JDH admin</b>'
    f'({os.environ.get("GIT_BRANCH")}/{os.environ.get("GIT_REVISION")})'
)
