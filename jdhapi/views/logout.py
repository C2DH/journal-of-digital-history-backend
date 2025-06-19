# views.py
from django.contrib.auth import logout
from django.http import JsonResponse


def custom_logout(request):
    logout(request)  # This clears the session
    return JsonResponse({"message": "Logged out successfully"})
