import json
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse

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


def parse_github_repo_url(repo_url: str):
    """ Parse GitHub URL """
    """ Accepts https://github.com/owner/repo or .git suffix """
    p = urlparse(
        repo_url,
    )
    path = p.path.lstrip("/").rstrip(".git")
    parts = path.split("/")
    owner = parts[0]
    pid = parts[1]

    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url!r}")
    return owner, pid


def get_default_branch(owner: str, repo: str) -> str:
    """ Get the default branch : main or another branch"""
    api = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api, headers=get_github_headers())
    if r.status_code != 200:
        raise ValueError(f"GitHub API error: {r.status_code} {r.text}")
    return r.json()["default_branch"]


def file_exists(owner: str, repo: str, branch: str, path: str) -> bool:
    """ Check if a file exist"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.head(url, params={"ref": branch}, headers=get_github_headers())
    return r.status_code == 200


def fetch_file_bytes(owner: str, repo: str, branch: str, path: str) -> bytes:
    """ Fetch a file from GitHub repository with the raw url"""
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = requests.get(raw, headers=get_github_headers())
    if r.status_code != 200:
        raise ValueError(f"Failed to fetch file from {raw}: {r.status_code}")
    return r.content


def parse_tweets_md(content: str) -> "tuple[list[str], list[str]]":
    """Parse a ``tweets.md`` file and return ``(thread_texts, independent_posts)``.

    Expected format::

        Post thread:
        1. First post text
        2. Second post text

        As independent posts:
        - A standalone post
    """
    thread_texts: list[str] = []
    independent: list[str] = []
    mode: "str | None" = None

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("Post thread:"):
            mode = "thread"
            continue
        if stripped.startswith("As independent posts:"):
            mode = "independent"
            continue
        if not stripped or mode is None:
            continue
        if mode == "thread" and stripped[0].isdigit() and "." in stripped:
            thread_texts.append(stripped.split(".", 1)[1].strip())
        elif mode == "independent" and stripped.startswith("-"):
            independent.append(stripped.lstrip("-").strip())

    return thread_texts, independent


def parse_times(arg, count: int) -> list:
    """Normalise *arg* to a list of exactly *count* timezone-aware datetimes.

    *arg* may be a JSON string, list/tuple, or bytes. A single timestamp is
    auto-expanded to *count* entries spaced 1 minute apart. A shorter list is
    extended by 1-minute increments from the last entry.
    """
    if arg is None:
        raise TypeError("Schedule times argument is required")
    if isinstance(arg, (list, tuple)):
        arr = list(arg)
    elif isinstance(arg, (bytes, bytearray)):
        arr = json.loads(arg.decode("utf-8"))
    elif isinstance(arg, str):
        arr = json.loads(arg)
    else:
        raise TypeError("Schedule must be a JSON string or a list of timestamps")

    if not isinstance(arr, list):
        raise ValueError(f"Schedule list must contain exactly {count} timestamps.")
    if len(arr) != count:
        if len(arr) == 1:
            try:
                base_dt = datetime.fromisoformat(arr[0])
            except Exception:
                raise TypeError(f"Invalid timestamp format: {arr[0]}")
            arr = [(base_dt + timedelta(minutes=i)).isoformat() for i in range(count)]
        elif len(arr) < count:
            try:
                last_dt = datetime.fromisoformat(arr[-1])
            except Exception:
                raise TypeError(f"Invalid timestamp format: {arr[-1]}")
            while len(arr) < count:
                last_dt = last_dt + timedelta(minutes=1)
                arr.append(last_dt.isoformat())
        else:
            raise ValueError(f"Schedule list has {len(arr)} timestamps but expected {count}")

    times = []
    for s in arr:
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            raise TypeError(f"Invalid timestamp format: {s}")
        if dt.tzinfo is None:
            raise ValueError(f"Timestamp '{s}' must include a timezone offset")
        times.append(dt)

    if any(times[i] > times[i + 1] for i in range(len(times) - 1)):
        raise ValueError("Schedule times must be in non-decreasing order.")
    return times