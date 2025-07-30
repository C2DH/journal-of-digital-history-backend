import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler


DELAY_BETWEEN_POSTS = 10  # 10 seconds

# GitHub-related functions


def parse_repo_url(repo_url: str):
    p = urlparse(repo_url)
    parts = p.path.lstrip("/").rstrip(".git").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    return parts[0], parts[1]


def github_api(path: str):
    return f"https://api.github.com{path}"


def get_default_branch(owner: str, repo: str) -> str:
    r = requests.get(github_api(f"/repos/{owner}/{repo}"))
    r.raise_for_status()
    return r.json()["default_branch"]


def fetch_file_bytes(owner: str, repo: str, branch: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = requests.get(url)
    r.raise_for_status()
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

GRAPH = "https://graph.facebook.com/v12.0"


def fb_upload_photo(page_id: str, token: str, img_bytes: bytes) -> str:
    files = {"source": ("img.jpg", img_bytes)}
    data = {"published": "false", "access_token": token}
    r = requests.post(f"{GRAPH}/{page_id}/photos", files=files, data=data)
    r.raise_for_status()
    return r.json()["id"]


def fb_post_feed(
    page_id: str, token: str, msg: str, link: str = None, img: bytes = None
) -> str:
    payload = {"message": msg}
    if link:
        payload["link"] = link
    if img:
        mid = fb_upload_photo(page_id, token, img)
        payload["attached_media"] = json.dumps([{"media_fbid": mid}])
    r = requests.post(
        f"{GRAPH}/{page_id}/feed", params={"access_token": token}, data=payload
    )
    r.raise_for_status()
    return r.json()["id"]


def fb_post_comment(post_id: str, token: str, msg: str) -> str:
    r = requests.post(
        f"{GRAPH}/{post_id}/comments",
        params={"access_token": token},
        data={"message": msg},
    )
    r.raise_for_status()
    return r.json()["id"]


# wrapper function


def retry(func, *args, **kwargs):
    attempt = 1
    while True:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Retry {attempt} failed: {e}, retrying in 5s...")
            attempt += 1
            time.sleep(DELAY_BETWEEN_POSTS)


# throttling

global_last = {"time": None}


def throttle():
    now = time.time()
    last = global_last["time"]
    if last:
        delta = now - last
        if delta < DELAY_BETWEEN_POSTS:
            time.sleep(DELAY_BETWEEN_POSTS - delta)
    global_last["time"] = time.time()


# posting

state = {}


def post_thread_item(ci, text, link, img, idx):
    throttle()
    page, tok = ci
    print(f"[{datetime.now(timezone.utc).isoformat()}] Thread item {idx+1}")
    if idx == 0:
        pid = retry(fb_post_feed, page, tok, text, link, img)
        state["parent"] = pid
        print(f"  Main post ID: {pid}")
    else:
        parent = state.get("parent")
        if parent:
            cid = retry(fb_post_comment, parent, tok, text)
            print(f"  Comment {idx} ID: {cid}")
        else:
            print("  No parent for comment")


def post_independent(ci, text, link, img, idx):
    throttle()
    page, tok = ci
    print(f"[{datetime.now(timezone.utc).isoformat()}] Independent {idx+1}")
    pid = retry(fb_post_feed, page, tok, text, link, img)
    print(f"  Independent post ID: {pid}")


# scheduling


def parse_times(arg, count):
    arr = json.loads(arg)
    if not isinstance(arr, list) or len(arr) != count:
        sys.exit(f"Expected {count} timestamps, got {len(arr)}")
    ts = []
    for s in arr:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            sys.exit(f"Timestamp {s} missing offset")
        ts.append(dt)
    if any(ts[i] > ts[i + 1] for i in range(len(ts) - 1)):
        sys.exit("Timestamps must be non-decreasing")
    return ts


# function to import


def launch_social_media_facebook(
    repo_url: str = "",
    image_file: str = "",
    branch: str = "",
    article_link: str = "",
    page_id: str = "",
    access_token: str = "",
    schedule_main="",
    schedule_independent="",
):
    if repo_url == "" or article_link == "" or page_id == "" or access_token == "":
        return "One of the mandatory fields is missing"
    parser = argparse.ArgumentParser(
        description="Schedule thread and independent posts from GitHub tweets.md"
    )

    args = parser.parse_args()
    setattr(args, "repo_url", repo_url)
    setattr(args, "link", article_link)
    setattr(args, "page_id", page_id)
    setattr(args, "access_token", access_token)

    if branch != "":
        setattr(args, "branch", branch)
    else:
        setattr(args, "branch", None)

    if image_file == "":
        setattr(args, "no_image", True)
    else:
        setattr(args, "no_image", None)
        setattr(args, "image_file", image_file)

    if schedule_main != "":
        if not isinstance(schedule_main, str):
            setattr(args, "schedule_main", json.dumps(schedule_main))
        else:
            setattr(args, "schedule_main", schedule_main)
    else:
        setattr(args, "schedule_main", None)

    if schedule_independent != "":
        if not isinstance(schedule_independent, str):
            setattr(args, "schedule_independent", json.dumps(schedule_independent))
        else:
            setattr(args, "schedule_independent", schedule_independent)
    else:
        setattr(args, "schedule_independent", None)

    main(ext_args=args)


# main


def main(ext_args: object = None):
    if ext_args is None:
        p = argparse.ArgumentParser()
        p.add_argument("repo_url")
        p.add_argument("image_file", nargs="?")
        p.add_argument("--branch")
        p.add_argument("--link", required=True)
        p.add_argument("--page-id", required=True)
        p.add_argument("--access-token", required=True)
        p.add_argument("--no-image", action="store_true")
        p.add_argument("--schedule-main")
        p.add_argument("--schedule-independent")
        args = p.parse_args()
    else:
        args = ext_args

    owner, repo = parse_repo_url(args.repo_url)
    branch = args.branch or get_default_branch(owner, repo)
    md = fetch_file_bytes(owner, repo, branch, "tweets.md").decode()
    thread_texts, independent_texts = parse_tweets_md(md)
    if not thread_texts:
        sys.exit("No thread items")

    img_bytes = None
    if not args.no_image and args.image_file:
        img_bytes = fetch_file_bytes(owner, repo, branch, args.image_file)

    client_info = (args.page_id, args.access_token)

    scheduler = BlockingScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        job_defaults={"misfire_grace_time": None},
    )

    # listener for the missed jobs, restarts in 10s
    def on_miss(event):
        print(f"Job {event.job_id} missed; retrying in 10s...")
        job = scheduler.get_job(event.job_id)
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc) + timedelta(seconds=10))

    scheduler.add_listener(on_miss, EVENT_JOB_MISSED)

    # building unified timeline
    now = datetime.now(timezone.utc)
    timeline = []
    # first thread entries
    if args.schedule_main:
        times = parse_times(args.schedule_main, len(thread_texts))
    else:
        times = [now] * len(thread_texts)
    for i, t in enumerate(times):
        timeline.append(
            (
                t,
                post_thread_item,
                [client_info, thread_texts[i], args.link, img_bytes, i],
                f"Thread {i+1}",
            )
        )
    # then independent posts
    if independent_texts:
        if args.schedule_independent:
            times2 = parse_times(args.schedule_independent, len(independent_texts))
        else:
            times2 = [now] * len(independent_texts)
        for j, t in enumerate(times2):
            timeline.append(
                (
                    t,
                    post_independent,
                    [client_info, independent_texts[j], args.link, img_bytes, j],
                    f"Independent {j+1}",
                )
            )
    # sorting by time
    timeline.sort(key=lambda x: x[0])

    jobs = []
    total = 0
    for seq, (rt, func, fargs, label) in enumerate(timeline):
        run_at = rt + timedelta(milliseconds=seq)
        if run_at <= now:
            print(
                f"Time {run_at.isoformat()} for {label} passed; executing immediately"
            )
            func(*fargs)
        else:
            jobs.append(scheduler.add_job(func, "date", run_date=run_at, args=fargs))
            print(f"Scheduled {label} at {run_at.isoformat()}")
            total += 1

    # shutdown switch
    if total > 0:

        def on_done(event):
            nonlocal total
            total -= 1
            if total <= 0:
                scheduler.shutdown(wait=False)

        scheduler.add_listener(on_done, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    if jobs:
        scheduler.start()


if __name__ == "__main__":
    main()


#####  Running standalone example:

# python3 facebook_script.py https://github.com/memerchik/Gqh2Bf5W4TdK
# --link https://journalofdigitalhistory.org/en/article/Gqh2Bf5W4TdK
# --page-id PAGE_ID_HERE
# --access-token TOKEN_HERE
# --no-image
# --schedule-main '["2025-07-29T12:46+02:00", "2025-07-29T12:46+02:00", "2025-07-29T12:46+02:00", "2025-07-29T12:48+02:00", "2025-07-29T12:48+02:00"]'
# --schedule-independent '["2025-07-29T12:47+02:00", "2025-07-29T12:48+02:00", "2025-07-29T12:48+02:00", "2025-07-29T12:48+02:00"]'

##### Usage example when imported into another file:

# from facebook_script import launch_social_media_facebook

# launch_social_media_facebook(access_token="TOKEN_HERE",
#                              page_id=PAGE_ID_HERE,
#                              article_link="https://journalofdigitalhistory.org/en/article/Gqh2Bf5W4TdK",
#                              repo_url="https://github.com/memerchik/Gqh2Bf5W4TdK",
#                              schedule_main=["2025-07-29T12:46+02:00", "2025-07-29T12:46+02:00", "2025-07-29T12:46+02:00", "2025-07-29T12:48+02:00", "2025-07-29T12:48+02:00"],
#                              schedule_independent=["2025-07-29T12:47+02:00", "2025-07-29T12:48+02:00", "2025-07-29T12:48+02:00", "2025-07-29T12:48+02:00"])
