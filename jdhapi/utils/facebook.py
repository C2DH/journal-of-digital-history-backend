import json
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from .bluesky import save_social_media_campaign_in_database
from .github_repository import (
    fetch_file_bytes,
    get_default_branch,
    parse_github_repo_url,
    parse_tweets_md,
)

logger = logging.getLogger(__name__)


DELAY_BETWEEN_POSTS = 10  # 10 seconds

GRAPH = "https://graph.facebook.com/v12.0"


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
    logger.info(f"FACEBOOK - Answer from post creation {r.text}")
    if r.status_code != 200:
        raise Exception(f"Post creation failed: {r.text}")
    return r.json()["id"]


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

    owner, pid = parse_github_repo_url(repo_url)
    branch = branch or get_default_branch(owner, pid)
    md = fetch_file_bytes(owner, pid, branch, "tweets.md").decode()
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
                raise ValueError("schedule timestamp must include timezone offset")
            now = datetime.now(timezone.utc)
            now = datetime.now(ZoneInfo("Europe/Luxembourg"))

            min_time = now + timedelta(minutes=10)
            if dt < min_time:
                raise ValueError("scheduled must be at least 10 minutes in the future")
            scheduled_time = dt

    post_id = fb_post_feed(
        page_id, access_token, text, article_link, img_bytes, scheduled_time
    )

    url = f"https://www.facebook.com/{post_id}"
    now = datetime.now(timezone.utc).isoformat()

    if scheduled_time:
        save_social_media_campaign_in_database(
            pid,
            platform="FACEBOOK",
            url=url,
            scheduled_time=scheduled_time.isoformat(),
            published_time=scheduled_time.isoformat(),
        )
    else:
        save_social_media_campaign_in_database(
            pid, platform="FACEBOOK", url=url, scheduled_time=None, published_time=now
        )

    return {
        "message": "Facebook campaign completed",
        "post_id": post_id,
        "scheduled_time": scheduled_time,
    }
