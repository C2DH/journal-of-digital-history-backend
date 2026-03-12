import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_github_headers():
    """Get GitHub API headers with token authentication if available."""
    try:
        headers = {}
        if hasattr(settings, "GITHUB_ACCESS_TOKEN") and settings.GITHUB_ACCESS_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_ACCESS_TOKEN}"
        return headers
    except ImportError:
        return {}


def is_reachable(url):
    get = requests.get(url, headers=get_github_headers())
    if get.status_code == 200:
        logger.info(f"{url}: is reachable")
        return True
    else:
        logger.info(f"{url}: is Not reachable, status_code: {get.status_code}")
        return False


def is_socialmediacover_exist(repository_url):
    # Get Url
    if repository_url:
        url_1 = repository_url + "/blob/main/socialmediacover.png"
        url_2 = repository_url + "/blob/main/socialmediacover.jpg"
        # if the request succeeds
        if is_reachable(url_1):
            return True
        else:
            if is_reachable(url_2):
                return True
            else:
                return False
    else:
        return False
