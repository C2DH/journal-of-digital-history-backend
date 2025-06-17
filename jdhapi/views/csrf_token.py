# views.py
from django.middleware.csrf import get_token
from django.http import JsonResponse


def get_csrf(request):
    csrf_token = get_token(request)
    return JsonResponse({"csrfToken": csrf_token})
