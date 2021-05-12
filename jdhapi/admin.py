import os
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Author,Abstract, Dataset



# Register your models here.
admin.site.register(Abstract)
admin.site.register(Dataset)
admin.site.register(Author)

admin.site.site_url = "/dashboard"

admin.site.site_header = mark_safe(
    '<b style="color:white">JDH admin</b>'
    f'({os.environ.get("GIT_BRANCH")}/{os.environ.get("GIT_REVISION")})'
)
