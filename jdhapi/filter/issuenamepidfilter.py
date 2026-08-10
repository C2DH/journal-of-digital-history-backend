from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _

class IssueNamePIDFilter(SimpleListFilter):
    title = _('Issue by name and PID')
    parameter_name = 'issue_by_name_and_pid'

    def lookups(self, request, model_admin):
        issues = model_admin.model.objects.all().values('issue__name', 'issue__pid')
        unique_issues = set((issue['issue__name'], issue['issue__pid']) for issue in issues)
        sorted_issues = sorted(unique_issues, key=lambda x: x[0])  # Sort by issue name
        return [(f"{name}_{pid}", f"{name} - {pid}") for name, pid in sorted_issues]

    def queryset(self, request, queryset):
        if self.value():
            name, pid = self.value().split('_')
            return queryset.filter(issue__name=name, issue__pid=pid)
        return queryset