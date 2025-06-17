# views.py
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views import View
import json


class CustomLoginView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:  # Only allow staff users to access admin
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid credentials or not authorized for admin",
                },
                status=401,
            )
