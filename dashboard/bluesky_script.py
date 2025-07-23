import argparse
import sys
import json
import time
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from atproto import Client, models
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from datetime import datetime, timezone

# Shared state for parent URI and CID
state = {}

BETWEEN_POST_DELAY = 5 # 5 seconds

BROWSER_UA = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Bluesky Cardyb/1.1; +mailto:support@bsky.app) Chrome/W.X.Y.Z Safari/537.36"
)

# Parse GitHub URL
# Accepts https://github.com/owner/repo or .git suffix
def parse_repo_url(repo_url: str):
    p = urlparse(repo_url)
    path = p.path.lstrip('/').rstrip('.git')
    parts = path.split('/')
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url!r}")
    return parts[0], parts[1]

# GitHub API helpers

def get_default_branch(owner: str, repo: str) -> str:
    api = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api)
    r.raise_for_status()
    return r.json()['default_branch']

def file_exists(owner: str, repo: str, branch: str, path: str) -> bool:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    r = requests.head(url, params={'ref': branch})
    return r.status_code == 200

def fetch_file_bytes(owner: str, repo: str, branch: str, path: str) -> bytes:
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    r = requests.get(raw)
    r.raise_for_status()
    return r.content

# Parse tweets.md for threads and independent posts
def parse_tweets_md(content: str):
    lines = content.splitlines()
    mode = None
    thread_texts, independent = [], []
    for line in lines:
        if line.strip().startswith('Post thread:'):
            mode = 'thread'; continue
        if line.strip().startswith('As independent posts:'):
            mode = 'independent'; continue
        if not line.strip() or mode is None:
            continue
        if mode == 'thread' and line.lstrip()[0].isdigit() and '.' in line:
            thread_texts.append(line.split('.',1)[1].strip())
        elif mode == 'independent' and line.lstrip().startswith('-'):
            independent.append(line.lstrip('-').strip())
    return thread_texts, independent

# Fetch metadata from link (OG tags)
def fetch_link_metadata(url: str):
    headers = {'User-Agent': BROWSER_UA}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    title_tag = soup.find('meta', property='og:title') or soup.find('title')
    desc_tag = soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'})
    img_tag = soup.find('meta', property='og:image')
    title = title_tag['content'] if title_tag and title_tag.has_attr('content') else (title_tag.text.strip() if title_tag else '')
    description = desc_tag['content'] if desc_tag and desc_tag.has_attr('content') else ''
    image_url = img_tag['content'] if img_tag and img_tag.has_attr('content') else None
    return title, description, image_url

# Fetch image
def fetch_image(url: str) -> bytes:
    headers = {'User-Agent': BROWSER_UA}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.content

# Get CID for replies
def get_record_cid(client, uri: str) -> str:
    did, collection, rkey = uri[len('at://'):].split('/')[:3]
    resp = client.com.atproto.repo.get_record({'repo': did, 'collection': collection, 'rkey': rkey})
    return resp.cid

# Post an item (main or reply)
def post_item(client, text, link=None, image_bytes=None, alt=None, index=0):
    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] Posting item index {index}")
    record = {
        '$type': 'app.bsky.feed.post',
        'text': text,
        'createdAt': now.isoformat()
    }
    # Main post: index 0
    if index == 0:
        if link:
            title, desc, img_url = fetch_link_metadata(link)
            thumb_ref = None
            if img_url:
                img_bytes = fetch_image(img_url)
                thumb_ref = client.upload_blob(img_bytes).blob
            ext = models.AppBskyEmbedExternal.External(
                uri=link,
                title=title,
                description=desc,
                thumb=thumb_ref
            )
            record['embed'] = models.AppBskyEmbedExternal.Main(external=ext)
        elif image_bytes:
            img_ref = client.upload_blob(image_bytes).blob
            img_mod = models.AppBskyEmbedImages.Image(alt=alt or '', image=img_ref)
            record['embed'] = models.AppBskyEmbedImages.Main(images=[img_mod])
        resp = client.com.atproto.repo.create_record({
            'repo': client.me.did,
            'collection': 'app.bsky.feed.post',
            'record': record
        })
        state['parent_uri'] = resp.uri
        state['parent_cid'] = resp.cid
        print(f"[{datetime.now(timezone.utc).isoformat()}] Main post URI: {resp.uri}")
        time.sleep(BETWEEN_POST_DELAY)
        return resp
    # Replies: index > 0
    parent_uri = state.get('parent_uri')
    parent_cid = state.get('parent_cid')
    if parent_uri and parent_cid:
        record['reply'] = {
            'root': {'uri': parent_uri, 'cid': parent_cid},
            'parent': {'uri': parent_uri, 'cid': parent_cid}
        }
        resp = client.com.atproto.repo.create_record({
            'repo': client.me.did,
            'collection': 'app.bsky.feed.post',
            'record': record
        })
        print(f"[{datetime.now(timezone.utc).isoformat()}] Reply {index} URI: {resp.uri}")
        time.sleep(BETWEEN_POST_DELAY)
        return resp
    # Fallback simple post
    resp = client.post(text)
    print(f"[{datetime.now(timezone.utc).isoformat()}] Simple post URI: {resp.uri}")
    time.sleep(BETWEEN_POST_DELAY)
    return resp

# Listener to shutdown scheduler when all jobs completed

def make_listener(total_jobs, scheduler):
    count = {'remaining': total_jobs}
    def listener(event):
        if event.code in (EVENT_JOB_EXECUTED, EVENT_JOB_ERROR):
            count['remaining'] -= 1
            if count['remaining'] <= 0:
                scheduler.shutdown(wait=False)
    return listener

# Parse schedule times
def parse_times(arg, count):
    arr = json.loads(arg)
    if not isinstance(arr, list) or len(arr) != count:
        sys.exit(f"Schedule list must contain exactly {count} timestamps for the {count} posts.")
    times = []
    for s in arr:
        try:
            dt = datetime.fromisoformat(s)
        except Exception:
            sys.exit(f"Invalid timestamp format: {s}")
        if dt.tzinfo is None:
            sys.exit(f"Timestamp '{s}' must include a timezone offset")
        times.append(dt)
    if any(times[i] > times[i+1] for i in range(len(times)-1)):
        sys.exit("Schedule times must be in non-decreasing order (simultaneous posts allowed).")
    return times


def launch_social_media(repo_url: str = "", image_file: str = "", branch: str = "", article_link: str = "", login: str = "", password: str = "", schedule_main = "", schedule_independent = ""):
    if repo_url == "" or article_link == "" or login == "" or password == "":
        return "One of the mandatory fields is missing"
    parser = argparse.ArgumentParser(
            description="Schedule thread and independent posts from GitHub tweets.md"
    )


    args=parser.parse_args()
    setattr(args, 'repo_url', repo_url)
    setattr(args, 'link', article_link)
    setattr(args, 'handle', login)
    setattr(args, 'app_pass', password)

    if branch != "":
        setattr(args, "branch", branch)
    else:
        setattr(args, "branch", None)

    if image_file == "":
        setattr(args, "no_image", True)
    else:
        setattr(args, "no_image", None)
        setattr(args, "image_file", image_file)
    
    if schedule_main !="":
        if not isinstance(schedule_main, str):
            setattr(args, "schedule_main", json.dumps(schedule_main))
        else:
            setattr(args, "schedule_main", schedule_main)
    else:
        setattr(args, "schedule_main", None)
    
    if schedule_independent!="":
        if not isinstance(schedule_independent, str):
            setattr(args, "schedule_independent", json.dumps(schedule_independent))
        else:
            setattr(args, "schedule_independent", schedule_independent)
    else:
        setattr(args, "schedule_independent", None)


    main(ext_args=args)


# Main entry
def main(ext_args: object = None):
    if ext_args == None:
        parser = argparse.ArgumentParser(
            description="Schedule thread and independent posts from GitHub tweets.md"
        )
        parser.add_argument('repo_url', help="GitHub repo URL")
        parser.add_argument('image_file', nargs='?', help="Optional image path in repo")
        parser.add_argument('--branch', help="Git branch; defaults to default branch")
        parser.add_argument('--link', required=True, help="Article URL for embeds")
        parser.add_argument('--no-image', action='store_true', help="Skip image upload")
        parser.add_argument('--handle', required=True, help="Your Bluesky handle")
        parser.add_argument('--app-pass', required=True, help="Your Bluesky app password")
        parser.add_argument('--schedule-main', help="JSON list of ISO times with offsets for thread items")
        parser.add_argument('--schedule-independent', help="JSON list of ISO times with offsets for independent items")
        args = parser.parse_args()
    else:
        args = ext_args

    owner, repo = parse_repo_url(args.repo_url)
    branch = args.branch or get_default_branch(owner, repo)
    tweets_md = 'tweets.md'
    if not file_exists(owner, repo, branch, tweets_md):
        sys.exit("Error: 'tweets.md' not found in repo root.")
    content = fetch_file_bytes(owner, repo, branch, tweets_md).decode('utf-8')
    thread_texts, independent_texts = parse_tweets_md(content)
    if not thread_texts:
        sys.exit("Error: No thread items under 'Post thread:'")

    image_bytes = None
    alt = None
    if not args.no_image and args.image_file:
        if not file_exists(owner, repo, branch, args.image_file):
            sys.exit(f"Error: Image '{args.image_file}' not found.")
        image_bytes = fetch_file_bytes(owner, repo, branch, args.image_file)
        alt = args.image_file

    client = Client()
    client.login(args.handle, args.app_pass)

    scheduler = BlockingScheduler(executors={'default': ThreadPoolExecutor(max_workers=1)})
    jobs = []

    # Schedule or post thread
    if args.schedule_main:
        times = parse_times(args.schedule_main, len(thread_texts))
        now = datetime.now(timezone.utc)
        future = [(idx, dt) for idx, dt in enumerate(times) if dt > now]
        if future:
            scheduler.add_listener(make_listener(len(future), scheduler), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        for idx, dt in enumerate(times):
            if dt <= now:
                print(f"Scheduled time {dt.isoformat()} for thread item {idx+1} has passed; posting immediately")
                post_item(client, thread_texts[idx], args.link, image_bytes, alt, idx)
            else:
                job = scheduler.add_job(post_item, 'date', run_date=dt,
                                        args=[client, thread_texts[idx], args.link, image_bytes, alt, idx])
                jobs.append(job)
                print(f"Scheduled thread item {idx+1} at {dt.isoformat()}")
    else:
        for idx, txt in enumerate(thread_texts):
            print(f"Posting thread item {idx+1} now")
            post_item(client, txt, args.link, image_bytes, alt, idx)

    # Schedule or post independent
    if independent_texts:
        if args.schedule_independent:
            times2 = parse_times(args.schedule_independent, len(independent_texts))
            now2 = datetime.now(timezone.utc)
            future2 = [(idx, dt) for idx, dt in enumerate(times2) if dt > now2]
            if future2:
                scheduler.add_listener(make_listener(len(future2), scheduler), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
            for idx, dt in enumerate(times2):
                if dt <= now2:
                    print(f"Scheduled time {dt.isoformat()} for independent item {idx+1} has passed; posting immediately")
                    post_item(client, independent_texts[idx], args.link, None, None, idx)
                else:
                    job = scheduler.add_job(post_item, 'date', run_date=dt,
                                            args=[client, independent_texts[idx], args.link, None, None, idx])
                    jobs.append(job)
                    print(f"Scheduled independent item {idx+1} at {dt.isoformat()}")
        else:
            for idx, txt in enumerate(independent_texts):
                print(f"Posting independent item {idx+1} now")
                post_item(client, txt, args.link)

    # Run scheduler if jobs pending
    if jobs:
        scheduler.start()

if __name__ == '__main__':
    main()



### Usage example when imported into a different file: 

# from bluesky_script import launch_social_media

# launch_social_media(article_link = "https://journalofdigitalhistory.org/en/article/Gqh2Bf5W4TdK", repo_url = "https://github.com/memerchik/Gqh2Bf5W4TdK", login = "***.bsky.social", password = "****", schedule_independent = ["2025-07-21T15:06+02:00", "2025-07-21T15:06+02:00"], schedule_main = ["2025-07-21T15:06+02:00", "2025-07-21T15:06+02:00"])

## The number of entries within "schedule_main" and "schedule_independent" must be the same as the number of tweets/posts within tweets.md file


### Usage example standalone: 

# python3 bluesky_script.py https://github.com/memerchik/Gqh2Bf5W4TdK --link https://journalofdigitalhistory.org/en/article/Gqh2Bf5W4TdK/ --handle ****.bsky.social --app-pass **** --no-image --schedule-main '["2025-07-21T16:47+02:00", "2025-07-21T16:48+02:00", "2025-07-21T16:48+02:00", "2025-07-21T16:48+02:00", "2025-07-21T16:48+02:00"]'