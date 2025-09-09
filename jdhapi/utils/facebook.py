import json
import logging
import requests
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


DELAY_BETWEEN_POSTS = 10  # 10 seconds

GRAPH = "https://graph.facebook.com/v12.0"


# GitHub-related functions
def parse_repo_url(repo_url: str):
    p = urlparse(repo_url)
    parts = p.path.lstrip("/").rstrip(".git").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    return parts[0], parts[1]


def get_default_branch(owner: str, repo: str) -> str:
    r = requests.get("https://api.github.com/repos/{owner}/{repo}")
    if r.status_code != 200:
        raise ValueError(
            f"GitHub repo not found: https://api.github.com/repos/{owner}/{repo}"
        )
    return r.json()["default_branch"]


def fetch_file_bytes(owner: str, repo: str, branch: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = requests.get(url)
    if r.status_code != 200:
        raise ValueError(f"File not found: {url}")
    return r.content


# MD parsing
def parse_tweets_md(md: str):
    thread, independent = [], []
    mode = None
    for line in md.splitlines():
        if line.startswith("Post thread:"):
            mode = "thread"
            continue
        if line.startswith("As independent posts:"):
            mode = "independent"
            continue
        if not line.strip() or mode is None:
            continue
        if mode == "thread" and line.lstrip()[0].isdigit() and "." in line:
            thread.append(line.split(".", 1)[1].strip())
        elif mode == "independent" and line.lstrip().startswith("-"):
            independent.append(line.lstrip("-").strip())
    return thread, independent


# Facebook API
def fb_upload_photo(page_id: str, token: str, img_bytes: bytes) -> str:
    files = {"source": ("img.jpg", img_bytes)}
    data = {"published": "false", "access_token": token}
    r = requests.post(f"{GRAPH}/{page_id}/photos", files=files, data=data)
    if r.status_code != 200:
        raise ValueError(f"Photo upload failed: {r.text}")
    return r.json()["id"]


def fb_post_feed(
    page_id: str,
    token: str,
    msg: str,
    link: str = None,
    img: bytes = None,
    scheduled_time: int = None,
) -> str:
    payload = {"message": msg}
    if link:
        payload["link"] = link
    if img:
        mid = fb_upload_photo(page_id, token, img)
        payload["attached_media"] = json.dumps([{"media_fbid": mid}])
    if scheduled_time:
        payload["published"] = "false"
        payload["scheduled_publish_time"] = scheduled_time
    r = requests.post(
        f"{GRAPH}/{page_id}/feed", params={"access_token": token}, data=payload
    )
    if r.status_code != 200:
        raise Exception(f"Post creation failed: {r.text}")
    return r.json()["id"]


# posting
state = {}


# scheduling
def parse_times(arg, count):
    arr = json.loads(arg)
    if not isinstance(arr, list) or len(arr) != count:
        logger.info(f"Expected {count} timestamps, got {len(arr)}")
    ts = []
    for s in arr:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            logger.info(f"Timestamp {s} missing offset")
        ts.append(dt)
    if any(ts[i] > ts[i + 1] for i in range(len(ts) - 1)):
        logger.info("Timestamps must be non-decreasing")
    return ts


def launch_social_media_facebook(
    repo_url: str = "",
    branch: str = "",
    article_link: str = "",
    page_id: str = "",
    access_token: str = "",
    schedule_main: str = "",
):
    if repo_url == "" or article_link == "" or page_id == "" or access_token == "":
        raise Exception(
            "repo_url, article_link, page_id and access_token are mandatory"
        )

    owner, repo = parse_repo_url(repo_url)
    branch = branch or get_default_branch(owner, repo)
    md = fetch_file_bytes(owner, repo, branch, "tweets.md").decode()
    text, _ = parse_tweets_md(md)
    if not text:
        raise Exception("No thread items")

    # Keep only the first numbered thread item (1.) — single post behavior
    text = [text[0]]

    # Normalize schedules to a single timestamp if a schedule was provided
    run_val = None
    img_bytes = None

    scheduled_time = None
    if schedule_main:
        run_val = None
        if isinstance(schedule_main, (list, tuple)):
            run_val = schedule_main[0] if schedule_main else None
        elif isinstance(schedule_main, (bytes, bytearray)):
            arr = json.loads(schedule_main.decode("utf-8"))
            run_val = arr[0] if isinstance(arr, list) and arr else None
        elif isinstance(schedule_main, str):
            try:
                parsed = json.loads(schedule_main)
                run_val = parsed[0] if isinstance(parsed, list) and parsed else None
            except Exception:
                run_val = schedule_main
        if run_val:
            dt = datetime.fromisoformat(run_val)
            if dt.tzinfo is None:
                raise ValueError("schedule_main timestamp must include timezone offset")
            now = datetime.now(timezone.utc)
            min_time = now + timedelta(minutes=10)
            if dt < min_time:
                raise ValueError(
                    "scheduled_publish_time must be at least 10 minutes in the future"
                )
            scheduled_time = dt

    post_id = fb_post_feed(
        page_id, access_token, text, article_link, img_bytes, scheduled_time
    )

    return {"post_id": post_id, "scheduled_time": scheduled_time}
