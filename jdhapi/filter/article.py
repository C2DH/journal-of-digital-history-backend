
from jdhapi.models import Article
from rest_framework import filters
from rest_framework.permissions import BasePermission


class IsStaffFilter(filters.BaseFilterBackend):
    """
    Filter that returns all articles for staff.
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_staff:
            return queryset  # Staff members can see all articles
        else:
            return queryset.filter(status=Article.Status.PUBLISHED)


class IsAuthenticatedPermission(BasePermission):
    """
    Permission to allow only authenticated users to access a non-published article.
    """

    def has_object_permission(self, request, view, obj):
        if obj.status == Article.Status.PUBLISHED:
            return True
        return request.user.is_authenticated

