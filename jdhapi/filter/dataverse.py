from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


class EmptyDataverseURLFilter(admin.SimpleListFilter):
    title = _('Empty Dataverse URL')
    parameter_name = 'empty_dataverse_url'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Has Empty Dataverse URL')),
            ('0', _('Has Dataverse URL')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(Q(dataverse_url__isnull=True) | Q(dataverse_url=''))
        elif self.value() == '0':
            return queryset.exclude(Q(dataverse_url__isnull=True) | Q(dataverse_url=''))
        return queryset
