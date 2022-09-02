import os
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Author, Abstract, Dataset, Article, Issue, Tag, Role
from .filter.languagetagfilter import LanguageTagFilter
from .tasks import save_article_fingerprint, save_article_specific_content, save_citation, save_libraries
from import_export.admin import ExportActionMixin


def save_notebook_fingerprint(modeladmin, request, queryset):
    for article in queryset:
        save_article_fingerprint.delay(article_id=article.pk)


save_notebook_fingerprint.short_description = "1: Generate fingerprint"


def save_notebook_specific_cell(modeladmin, request, queryset):
    for article in queryset:
        save_article_specific_content.delay(article_id=article.pk)


save_notebook_specific_cell.short_description = "2: Generate preload information"


def save_article_citation(modeladmin, request, queryset):
    for article in queryset:
        save_citation.delay(article_id=article.pk)


save_article_citation.short_description = "3: Generate citation"


def save_article_package(modeladmin, request, queryset):
    for article in queryset:
        save_libraries.delay(article_id=article.pk)


save_article_package.short_description = "4: Generate tags TOOL/NARRATIVE"


class AbstractAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ['title', 'contact_email', 'submitted_date', 'status']
    list_filter = ('status',)


class AuthorAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ['lastname', 'firstname', 'affiliation', 'orcid', 'email']


class IssueAdmin(admin.ModelAdmin):
    list_display = ['name', 'volume', 'issue', 'status', 'publication_date']


class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ('category', LanguageTagFilter,)
    # list_filter = ('category',)


class ArticleAdmin(admin.ModelAdmin):
    list_display = ['abstract_pid', 'issue', 'abstract_title', 'status']
    list_filter = ('issue', 'status', 'copyright_type')
    actions = [save_notebook_fingerprint, save_notebook_specific_cell, save_article_citation, save_article_package]

    def abstract_pid(self, obj):
        return obj.abstract.pid
    abstract_pid.short_description = 'Pid'

    def abstract_title(self, obj):
        return obj.abstract.title
    abstract_title.short_description = 'Title'


# Register your models here.
admin.site.register(Abstract, AbstractAdmin)
admin.site.register(Dataset)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(Issue, IssueAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Role)
admin.site.site_url = "/dashboard"
admin.site.site_header = mark_safe(
    '<b style="color:white">JDH admin</b>'
    f'({os.environ.get("GIT_BRANCH")}/{os.environ.get("GIT_REVISION")})'
)
