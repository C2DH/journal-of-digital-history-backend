import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings


@api_view(["GET"])
def check_github_id(request, username):
    """
    Check if a GitHub username exists by making a call to the GitHub API.
    """
    github_api_url = f"https://api.github.com/users/{username}"
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_ACCESS_TOKEN}"  # Add the token here
    }
    try:
        response = requests.get(github_api_url, headers=headers)
        if response.status_code == 200:
            return Response({"exists": True, "data": response.json()}, status=200)
        elif response.status_code == 404:
            return Response(
                {"exists": False, "message": f"GitHub user '{username}' not found."},
                status=404,
            )
        else:
            return Response(
                {
                    "error": "Unexpected error occurred while contacting GitHub API.",
                    "status_code": response.status_code,
                },
                status=response.status_code,
            )
    except requests.exceptions.RequestException as e:
        return Response(
            {"error": "Failed to connect to GitHub API.", "details": str(e)}, status=500
        )
