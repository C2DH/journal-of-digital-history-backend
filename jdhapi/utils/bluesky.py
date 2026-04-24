import logging
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from atproto import Client, models
from bs4 import BeautifulSoup
from django.conf import settings
from jdhapi.models import Article, SocialMedia

from .github_repository import (
    fetch_file_bytes,
    file_exists,
    get_default_branch,
    parse_github_repo_url,
    parse_times,
    parse_tweets_md,
)
from .scheduler import get_background_scheduler, make_listener

logger = logging.getLogger(__name__)

# Shared state for parent URI and CID
state = {}

BETWEEN_POST_DELAY = 5  # 5 seconds

BROWSER_UA = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Bluesky Cardyb/1.1; "
    "+mailto:support@bsky.app) Chrome/W.X.Y.Z Safari/537.36"
)

BLUESKY_JDH_ACCOUNT = settings.BLUESKY_JDH_ACCOUNT


def fetch_link_metadata(url: str):
    """Fetch metadata from an url with OG tags"""
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


def fetch_image(url: str) -> bytes:
    """Fetch image"""
    headers = {"User-Agent": BROWSER_UA}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code != 200 or "image" not in r.headers.get("Content-Type", ""):
        raise ValueError(f"Failed to fetch image from {url}")
    return r.content


def get_rkey(uri: str) -> str:
    """Take the key of a Bluesky post"""
    did, collection, rkey = uri[len("at://") :].split("/")[:3]
    return rkey


def post_item(pid, client, text, link=None, image_bytes=None, alt=None, index=0):
    """Post an item, main or thread reply"""
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
        save_social_media_campaign_in_database(
            pid, resp, scheduled_time=None, published_time=now.isoformat()
        )

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
    save_social_media_campaign_in_database(
        pid, resp, scheduled_time=None, published_time=now.isoformat()
    )

    time.sleep(BETWEEN_POST_DELAY)

    return resp


def post_item_scheduled(
    pid, login, password, text, link=None, image_bytes=None, alt=None, index=0
):
    logger.info("Scheduled job — logging into Bluesky for index=%s", index)
    client = Client()
    try:
        client.login(login, password)
    except Exception:
        logger.exception("Scheduled job - login failed for index=%s", index)
        raise
    return post_item(pid, client, text, link, image_bytes, alt, index)


def save_social_media_campaign_in_database(
    pid: str, response, scheduled_time: str, published_time: str, platform="BLUESKY"
   
):
    article_selected = Article.objects.get(abstract__pid=pid)

    if scheduled_time:
        SocialMedia.objects.create(
            article=article_selected,
            platform=platform,
            url=None,
            scheduled_time=scheduled_time,
            published_time=None,
        )

    if published_time:
        if response:
            logger.info(
                f"Bluesky give us back the response.uri:{response.uri} for this article {pid}"
            )
            rkey = get_rkey(response.uri)
            url_main_post = (
                f"https://bsky.app/profile/{BLUESKY_JDH_ACCOUNT}/post/{rkey}"
            )
            logger.info(f"Bluesky post created at this url: {url_main_post}")

            SocialMedia.objects.filter(
                article=article_selected, platform="BLUESKY"
            ).update(url=url_main_post, published_time=published_time)
        else:
            raise Exception("No response given from Bluesky API")


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

    owner, pid = parse_github_repo_url(repo_url)
    branch = get_default_branch(owner, pid) or branch

    if not file_exists(owner, pid, branch, "tweets.md"):
        raise Exception("'tweets.md' not found in repository.")

    content = fetch_file_bytes(owner, pid, branch, "tweets.md").decode("utf-8")
    thread_texts, unique_text = parse_tweets_md(content)

    if not thread_texts and not unique_text:
        raise Exception(
            "Tweets.md not formatted as'Post thread:' or with independent text."
        )

    image_bytes = None
    alt = None

    client = Client()
    client.login(login, password)

    scheduler = get_background_scheduler()
    jobs = []

    # Schedule or post thread
    if schedule_main:
        all_posts = thread_texts + unique_text
        times = parse_times(schedule_main, len(all_posts))
        now = datetime.now(ZoneInfo("Europe/Luxembourg"))

        save_social_media_campaign_in_database(
            pid=pid, response=None, scheduled_time=times[0].isoformat(), published_time=None
        )

        future_count = sum(1 for dt in times if dt > now)
        if future_count:
            scheduler.add_listener(
                make_listener(future_count, scheduler),
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR,
            )

        for idx, (text, dt) in enumerate(zip(all_posts, times)):
            # Thread items chain as replies; independent posts are always standalone
            post_index = idx if idx < len(thread_texts) else 0

            if dt <= now:
                logger.info(
                    f"Scheduled time {dt.isoformat()} has passed; posting immediately"
                )
                post_item(pid, client, text, article_link, image_bytes, alt, post_index)
            else:
                job = scheduler.add_job(
                    post_item_scheduled,
                    "date",
                    run_date=dt,
                    args=[
                        pid,
                        login,
                        password,
                        text,
                        article_link,
                        image_bytes,
                        alt,
                        post_index,
                    ],
                )
                jobs.append(job)
                logger.info(f"Scheduled item {idx + 1} at {dt.isoformat()}")
    else:
        for idx, txt in enumerate(thread_texts):
            logger.info(f"Posting thread item {idx + 1} now")
            post_item(pid, client, txt, article_link, image_bytes, alt, idx)
        for txt in unique_text:
            logger.info("Posting independent post now")
            post_item(pid, client, txt, article_link, image_bytes, alt, 0)

    return {
        "message": "Bluesky campaign completed",
        "total_posts": len(thread_texts),
        "scheduled_jobs": len(jobs),
    }
