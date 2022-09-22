from pickle import FALSE
import requests
import logging

logger = logging.getLogger(__name__)


def is_socialmediacover_exist(repository_url):
    # Get Url
    if repository_url:
        url = repository_url + "/blob/main/socialmediacover.png"
        get = requests.get(url)
        # if the request succeeds
        if get.status_code == 200:
            logger.info(f"{url}: is reachable")
            return True
        else:
            logger.info(f"{url}: is Not reachable, status_code: {get.status_code}")
            return False
    else:
        return False
