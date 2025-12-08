import json
import logging
import requests
import time
from bs4 import BeautifulSoup
from atproto import Client, models
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from django.conf import settings
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Shared state for parent URI and CID
state = {}

BETWEEN_POST_DELAY = 5  # 5 seconds

BROWSER_UA = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Bluesky Cardyb/1.1; "
    "+mailto:support@bsky.app) Chrome/W.X.Y.Z Safari/537.36"
)

_background_scheduler = None


def get_github_headers():
    """Get GitHub API headers with token authentication if available."""
    try:
        headers = {}
        if hasattr(settings, "GITHUB_ACCESS_TOKEN") and settings.GITHUB_ACCESS_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_ACCESS_TOKEN}"
        return headers
    except ImportError:
        return {}


def _get_background_scheduler():
    global _background_scheduler
    if _background_scheduler is None or not getattr(_background_scheduler, "running", False):
        _background_scheduler = BackgroundScheduler(
            timezone=timezone.utc,
            executors={"default": ThreadPoolExecutor(max_workers=3)},
            job_defaults={"coalesce": False, "max_instances": 3},
        )
        _background_scheduler.start()
        logger.info("Background scheduler started")
    return _background_scheduler


# Parse GitHub URL
# Accepts https://github.com/owner/repo or .git suffix
def parse_repo_url(repo_url: str):
    p = urlparse(
        repo_url,
    )
    path = p.path.lstrip("/").rstrip(".git")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url!r}")
    return parts[0], parts[1]


# GitHub API helpers
def get_default_branch(owner: str, repo: str) -> str:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api, headers=get_github_headers())
    if r.status_code != 200:
        raise ValueError(f"GitHub API error: {r.status_code} {r.text}")
    return r.json()["default_branch"]


def file_exists(owner: str, repo: str, branch: str, path: str) -> bool:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.head(url, params={"ref": branch}, headers=get_github_headers())
    return r.status_code == 200


def url_exists(url: str) -> bool:
    r = requests.head(url)
    return r.status_code == 200


def fetch_file_bytes(owner: str, repo: str, branch: str, path: str) -> bytes:
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = requests.get(raw, headers=get_github_headers())
    if r.status_code != 200:
        raise ValueError(f"Failed to fetch file from {raw}: {r.status_code}")
    return r.content


# Parse tweets.md for threads and independent posts
def parse_tweets_md(content: str):
    lines = content.splitlines()
    mode = None
    thread_texts, independent = [], []
    for line in lines:
        if line.strip().startswith("Post thread:"):
            mode = "thread"
            continue
        if not line.strip() or mode is None:
            continue
        if mode == "thread" and line.lstrip()[0].isdigit() and "." in line:
            thread_texts.append(line.split(".", 1)[1].strip())
        elif mode == "independent" and line.lstrip().startswith("-"):
            independent.append(line.lstrip("-").strip())
    return thread_texts, independent


# Fetch metadata from link (OG tags)
def fetch_link_metadata(url: str):
    headers = {"User-Agent": BROWSER_UA}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200:
        raise ValueError(f"Failed to fetch URL {url}: {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    title_tag = soup.find("meta", property="og:title") or soup.find("title")
    desc_tag = soup.find("meta", property="og:description") or soup.find(
        "meta", attrs={"name": "description"}
    )
    img_tag = soup.find("meta", property="og:image")
    title = (
        title_tag["content"]
        if title_tag and title_tag.has_attr("content")
        else (title_tag.text.strip() if title_tag else "")
    )
    description = (
        desc_tag["content"] if desc_tag and desc_tag.has_attr("content") else ""
    )
    image_url = img_tag["content"] if img_tag and img_tag.has_attr("content") else None
    return title, description, image_url


# Fetch image
def fetch_image(url: str) -> bytes:
    headers = {"User-Agent": BROWSER_UA}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200 or "image" not in r.headers.get("Content-Type", ""):
        raise ValueError(f"Failed to fetch image from {url}")
    return r.content


# Get CID for replies
def get_record_cid(client, uri: str) -> str:
    did, collection, rkey = uri[len("at://") :].split("/")[:3]
    resp = client.com.atproto.repo.get_record(
        {"repo": did, "collection": collection, "rkey": rkey}
    )
    if not resp or not resp.cid:
        raise ValueError(f"Failed to get record CID for {uri}")
    return resp.cid


# Post an item (main or reply)
def post_item(client, text, link=None, image_bytes=None, alt=None, index=0):
    now = datetime.now(timezone.utc)
    logger.info(f"Posting item index {index}")

    record = {"$type": "app.bsky.feed.post", "text": text, "createdAt": now.isoformat()}
    # Main post: index 0
    if index == 0:
        if link:
            title, desc, img_url = fetch_link_metadata(link)
            thumb_ref = None
            if img_url:
                img_bytes = fetch_image(img_url)
                thumb_ref = client.upload_blob(img_bytes).blob
            ext = models.AppBskyEmbedExternal.External(
                uri=link, title=title, description=desc, thumb=thumb_ref
            )
            record["embed"] = models.AppBskyEmbedExternal.Main(external=ext)
        elif image_bytes:
            img_ref = client.upload_blob(image_bytes).blob
            img_mod = models.AppBskyEmbedImages.Image(alt=alt or "", image=img_ref)
            record["embed"] = models.AppBskyEmbedImages.Main(images=[img_mod])
        resp = client.com.atproto.repo.create_record(
            {
                "repo": client.me.did,
                "collection": "app.bsky.feed.post",
                "record": record,
            }
        )
        state["parent_uri"] = resp.uri
        state["parent_cid"] = resp.cid

        logger.info(f"Main post URI: {resp.uri}")

        time.sleep(BETWEEN_POST_DELAY)
        return resp

    # Replies: index > 0
    parent_uri = state.get("parent_uri")
    parent_cid = state.get("parent_cid")
    if parent_uri and parent_cid:
        record["reply"] = {
            "root": {"uri": parent_uri, "cid": parent_cid},
            "parent": {"uri": parent_uri, "cid": parent_cid},
        }
        resp = client.com.atproto.repo.create_record(
            {
                "repo": client.me.did,
                "collection": "app.bsky.feed.post",
                "record": record,
            }
        )
        logger.info(f"Reply {index} URI: {resp.uri}")

        time.sleep(BETWEEN_POST_DELAY)
        return resp

    # Fallback simple post
    resp = client.post(text)
    logger.info(f"Simple post URI: {resp.uri}")
    time.sleep(BETWEEN_POST_DELAY)

    return resp

def post_item_scheduled(login, password, text, link=None, image_bytes=None, alt=None, index=0):
    logger.info("Scheduled job running — logging into Bluesky for index=%s", index)
    client = Client()
    try:
        client.login(login, password)
    except Exception:
        logger.exception("Scheduled job: login failed for index=%s", index)
        raise

    try:
        return post_item(client, text, link, image_bytes, alt, index)
    except Exception:
        logger.exception("Scheduled job failed for index=%s", index)
        raise


# Listener to shutdown scheduler when all jobs completed
def make_listener(total_jobs, scheduler):
    count = {"remaining": total_jobs}

    def listener(event):
        if event.code in (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR):
            count["remaining"] -= 1
            if count["remaining"] <= 0:
                logger.info("All scheduled jobs for this campaign finished.")
                #leave global scheduler running
    return listener


# Parse schedule times
def parse_times(arg, count):
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
            raise Exception(f"Timestamp '{s}' must include a timezone offset")
        times.append(dt)
    if any(times[i] > times[i + 1] for i in range(len(times) - 1)):
        raise Exception(
            "Schedule times must be in non-decreasing order (simultaneous posts allowed)."
        )
    return times


def launch_social_media_bluesky(
    repo_url: str = "",
    branch: str = "",
    article_link: str = "",
    login: str = "",
    password: str = "",
    schedule_main: str = "",
):

    if not repo_url or not article_link or not login or not password:
        raise Exception("repo_url, article_link, login and password are required")

    owner, repo = parse_repo_url(repo_url)
    branch = get_default_branch(owner, repo) or branch
    tweets_md = "tweets.md"

    if not file_exists(owner, repo, branch, tweets_md):
        raise Exception("'tweets.md' not found in repo root.")

    content = fetch_file_bytes(owner, repo, branch, tweets_md).decode("utf-8")
    thread_texts, _ = parse_tweets_md(content)

    if not thread_texts:
        raise Exception("No thread items under 'Post thread:'")

    image_bytes = None
    alt = None

    client = Client()
    client.login(login, password)

    scheduler = _get_background_scheduler()
    jobs = []

    # Schedule or post thread
    if schedule_main:
        times = parse_times(schedule_main, len(thread_texts))
        now = datetime.now(timezone.utc)
        
        # Handle CEST/CET timezone 
        now = datetime.now(ZoneInfo("Europe/Luxembourg"))
   
        future = [(idx, dt) for idx, dt in enumerate(times) if dt > now]
  
        if future:

            scheduler.add_listener(
                make_listener(len(future), scheduler),
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
            )
        for idx, dt in enumerate(times):
            if dt <= now:
               
                logger.info(
                    f"Scheduled time {dt.isoformat()} for thread item {idx + 1} has passed; posting immediately"
                )
                post_item(
                    client, thread_texts[idx], article_link, image_bytes, alt, idx
                )
            else:
                job = scheduler.add_job(
                    post_item_scheduled,
                    "date",
                    run_date=dt,
                    args=[
                        login, 
                        password,
                        thread_texts[idx],
                        article_link,
                        image_bytes,
                        alt,
                        idx,
                    ],
                )
                jobs.append(job)
                logger.info(f"Scheduled thread item {idx + 1} at {dt.isoformat()}")
    else:
        for idx, txt in enumerate(thread_texts):
            logger.info(f"Posting thread item {idx + 1} now")
            post_item(client, txt, article_link, image_bytes, alt, idx)

    return {
        "message": "Bluesky campaign completed",
        "total_posts": len(thread_texts),
        "scheduled_jobs": len(jobs),
    }