import os
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Author, Abstract, Dataset, Article, Issue, Tag, Role
from .tasks import save_article_fingerprint, save_article_specific_content


def save_notebook_fingerprint(modeladmin, request, queryset):
    for article in queryset:
        save_article_fingerprint.delay(article_id=article.pk)


save_notebook_fingerprint.short_description = "Save notebook fingerprint in fingerprint"


def save_notebook_specific_cell(modeladmin, request, queryset):
    for article in queryset:
        save_article_specific_content.delay(article_id=article.pk)


save_notebook_specific_cell.short_description = "Save notebook specific tagged cells in data"


class AbstractAdmin(admin.ModelAdmin):
    list_display = ['title', 'status']
    list_filter = ('status',)


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['issue', 'abstract_title', 'status']
    list_filter = ('issue', 'status')
    actions = [save_notebook_fingerprint, save_notebook_specific_cell]

    def abstract_title(self, obj):
        return obj.abstract.title
    abstract_title.short_description = 'Title'


# Register your models here.
admin.site.register(Abstract, AbstractAdmin)
admin.site.register(Dataset)
admin.site.register(Author)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Issue)
admin.site.register(Tag)
admin.site.register(Role)
admin.site.site_url = "/dashboard"
admin.site.site_header = mark_safe(
    '<b style="color:white">JDH admin</b>'
    f'({os.environ.get("GIT_BRANCH")}/{os.environ.get("GIT_REVISION")})'
)
