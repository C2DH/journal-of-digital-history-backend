from pickle import FALSE
import requests
import logging

logger = logging.getLogger(__name__)


def is_reachable(url):
    get = requests.get(url)
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
        get_1 = requests.get(url_1)
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
