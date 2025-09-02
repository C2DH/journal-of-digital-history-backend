import json
import logging
import time
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from atproto import Client, models
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Shared state for parent URI and CID
state = {}

BETWEEN_POST_DELAY = 5  # 5 seconds

BROWSER_UA = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Bluesky Cardyb/1.1; "
    "+mailto:support@bsky.app) Chrome/W.X.Y.Z Safari/537.36"
)


# Parse GitHub URL
# Accepts https://github.com/owner/repo or .git suffix
def parse_repo_url(repo_url: str):
    p = urlparse(repo_url)
    path = p.path.lstrip("/").rstrip(".git")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url!r}")
    return parts[0], parts[1]


# GitHub API helpers
def get_default_branch(owner: str, repo: str) -> str:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api)
    if r.status_code != 200:
        raise ValueError(f"GitHub API error: {r.status_code} {r.text}")
    return r.json()["default_branch"]


def file_exists(owner: str, repo: str, branch: str, path: str) -> bool:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.head(url, params={"ref": branch})
    return r.status_code == 200


def fetch_file_bytes(owner: str, repo: str, branch: str, path: str) -> bytes:
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = requests.get(raw)
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
        if line.strip().startswith("As independent posts:"):
            mode = "independent"
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
    logger.info("Posting item index {index}")

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

        logger.info("Main post URI: {resp.uri}")

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
        logger.info("Reply {index} URI: {resp.uri}")

        time.sleep(BETWEEN_POST_DELAY)
        return resp

    # Fallback simple post
    resp = client.post(text)
    logger.info("Simple post URI: {resp.uri}")
    time.sleep(BETWEEN_POST_DELAY)

    return resp


# Listener to shutdown scheduler when all jobs completed
def make_listener(total_jobs, scheduler):
    count = {"remaining": total_jobs}

    def listener(event):
        if event.code in (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR):
            count["remaining"] -= 1
            if count["remaining"] <= 0:
                scheduler.shutdown(wait=False)

    return listener


# Parse schedule times
def parse_times(arg, count):
    arr = json.loads(arg)
    if not isinstance(arr, list) or len(arr) != count:
        raise Exception(
            "Schedule list must contain exactly {count} timestamps for the {count} posts."
        )

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
    image_file: str = "",
    branch: str = "",
    article_link: str = "",
    login: str = "",
    password: str = "",
    schedule_main="",
    schedule_independent="",
):

    if not repo_url or not article_link or not login or not password:
        raise ValueError("repo_url, article_link, login and password are required")

    no_image = not bool(image_file)

    owner, repo = parse_repo_url(repo_url)
    branch = branch or get_default_branch(owner, repo)
    tweets_md = "tweets.md"

    if not file_exists(owner, repo, branch, tweets_md):
        raise Exception("'tweets.md' not found in repo root.")

    content = fetch_file_bytes(owner, repo, branch, tweets_md).decode("utf-8")
    thread_texts, independent_texts = parse_tweets_md(content)

    if not thread_texts:
        raise Exception("No thread items under 'Post thread:'")

    image_bytes = None
    alt = None
    if not no_image and image_file:
        if not file_exists(owner, repo, branch, image_file):
            raise Exception("Image '{args.image_file}' not found.")
        image_bytes = fetch_file_bytes(owner, repo, branch, image_file)
        alt = image_file

    client = Client()
    client.login(login, password)

    scheduler = BlockingScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)}
    )
    jobs = []

    # Schedule or post thread
    if schedule_main:
        times = parse_times(schedule_main, len(thread_texts))
        now = datetime.now(timezone.utc)
        future = [(idx, dt) for idx, dt in enumerate(times) if dt > now]
        if future:
            scheduler.add_listener(
                make_listener(len(future), scheduler),
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
            )
        for idx, dt in enumerate(times):
            if dt <= now:
                # logger.info(
                #     f"Scheduled time {dt.isoformat()} for thread item {idx + 1} has passed; posting immediately"
                # )
                post_item(
                    client, thread_texts[idx], article_link, image_bytes, alt, idx
                )
            else:
                job = scheduler.add_job(
                    post_item,
                    "date",
                    run_date=dt,
                    args=[
                        client,
                        thread_texts[idx],
                        article_link,
                        image_bytes,
                        alt,
                        idx,
                    ],
                )
                jobs.append(job)
                # logger.info(f"Scheduled thread item {idx + 1} at {dt.isoformat()}")
    else:
        for idx, txt in enumerate(thread_texts):
            # logger.info(f"Posting thread item {idx + 1} now")
            post_item(client, txt, article_link, image_bytes, alt, idx)

    # Schedule or post independent
    if independent_texts:
        if schedule_independent:
            times2 = parse_times(schedule_independent, len(independent_texts))
            now2 = datetime.now(timezone.utc)
            future2 = [(idx, dt) for idx, dt in enumerate(times2) if dt > now2]
            if future2:
                scheduler.add_listener(
                    make_listener(len(future2), scheduler),
                    EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
                )
            for idx, dt in enumerate(times2):
                if dt <= now2:
                    # logger.info(
                    #     (
                    #         f"Scheduled time {dt.isoformat()} for independent item "
                    #         f"{idx + 1} has passed; posting immediately"
                    #     )
                    # )
                    post_item(
                        client, independent_texts[idx], article_link, None, None, idx
                    )
                else:
                    job = scheduler.add_job(
                        post_item,
                        "date",
                        run_date=dt,
                        args=[
                            client,
                            independent_texts[idx],
                            article_link,
                            None,
                            None,
                            idx,
                        ],
                    )
                    jobs.append(job)
                    # logger.info(
                    #     f"Scheduled independent item {idx + 1} at {dt.isoformat()}"
                    # )
        else:
            for idx, txt in enumerate(independent_texts):
                # logger.info(f"Posting independent item {idx + 1} now")
                post_item(client, txt, article_link)

    # Run scheduler if jobs pending
    if jobs:
        scheduler.start()

    return {
        "message": "Bluesky campaign completed",
        "total_posts": len(thread_texts) + len(independent_texts),
        "scheduled_jobs": len(jobs),
    }
