# function that can be used in models live here
import json
import requests
from django.core.mail import send_mail
import re
import logging
from django.conf import settings  # import the settings file

logger = logging.getLogger(__name__)


def get_notebook_from_raw_github(raw_url):
    logger.info(
        f'get_notebook_from_raw_github - parsing url: {raw_url}')
    r = requests.get(raw_url)
    return r.json()


def get_notebook_from_github(
    repository_url, host='https://raw.githubusercontent.com'
):
    logger.info(
        f'get_notebook_from_github - parsing repository_url: {repository_url}')
    result = re.search(
        r'github\.com\/([^\/]+)\/([^\/]+)\/(blob\/)?(.*\.ipynb$)',
        repository_url
    )
    github_user = result.group(1)
    github_repo = result.group(2)
    github_filepath = result.group(4)
    raw_url = f'{host}/{github_user}/{github_repo}/{github_filepath}'
    # https://raw.githubusercontent.com/jdh-observer/jdh001-WBqfZzfi7nHK/blob/8315a108416f4a5e9e6da0c5e9f18b5e583ed825/scripts/Digital_epigraphy_cite2c_biblio.ipynb
    # Match github.com/<github_user abc>/<github_filepath XXX/yyy/zzz.ipynb>
    # and exclude the `/blob/` part of the url if any.
    # then extract the gighub username nd the filepath to download
    # conveniently from githubusercontent server.
    logger.info(f'get_notebook_from_github - requesting raw_url: {raw_url}...')
    return get_notebook_from_raw_github(raw_url)


def get_notebook_stats(raw_url):
    notebook = get_notebook_from_raw_github(raw_url=raw_url)
    logger.info(f'get_notebook_stats - notebook loaded: {raw_url}')

    cells = notebook.get('cells')
    # output
    cells_stats = []
    countContributors = 0
    # loop through cells and save relevant informations
    for cell in cells:
        c = {'type': cell['cell_type']}
        # just skip if it's empty
        source = cell.get('source', [])
        if not source:
            continue
        contents = ''.join(cell.get('source'))
        # check cell metadata
        tags = cell.get('metadata').get('tags', [])
        if 'hidden' in tags:
            continue
        if 'contributor' in tags:
            countContributors += 1
        c['countChars'] = len(''.join(source))
        c['isMetadata'] = any(tag in [
            'title', 'abstract', 'contributor', 'disclaimer', 'keywords'
        ] for tag in tags)
        c['isHermeneutic'] = any(tag in [
            'hermeneutics', 'hermeneutics-step'
        ] for tag in tags)
        c['isFigure'] = any(tag.startswith('figure-') for tag in tags)
        c['isTable'] = any(tag.startswith('table-') for tag in tags)
        c['isHeading'] = cell['cell_type'] == 'markdown' and re.match(
            r'\s*#+\s', contents) is not None
        cells_stats.append(c)
        # does it contains a cite2c marker?
        markers = re.findall(r'data-cite=[\'"][^\'"]+[\'"]', contents)
        c['countRefs'] = len(markers)

    result = {
        'stats': {
            'countRefs': sum([
                c['countRefs'] for c in cells_stats]),
            # 'countLines': sum([c['countLines'] for c in cells_stats]),
            'countChars': sum([
                c['countChars'] for c in cells_stats]),
            'countContributors': countContributors,
            'countHeadings': sum([
                c['isHeading'] for c in cells_stats]),
            'countHermeneuticCells': sum([
                c['isHermeneutic'] for c in cells_stats]),
            'countCodeCells': sum([
                c['type'] == 'code' for c in cells_stats]),
            'countCells': len(cells_stats),
            'extentChars': [
                min([c['countChars'] for c in cells_stats]),
                max([c['countChars'] for c in cells_stats])],
            'extentRefs': [
                min([c['countRefs'] for c in cells_stats]),
                max([c['countRefs'] for c in cells_stats])]
        },
        'cells': cells_stats
    }

    return result


def get_notebook_specifics_tags(raw_url):
    selected_tags = ['title', 'abstract', 'contributor']
    countTagsFound = 0
    notebook = get_notebook_from_raw_github(raw_url=raw_url)
    logger.info(f'get_notebook_specifics_tags - notebook loaded: {raw_url}')
    cells = notebook.get('cells')
    # output
    cells_sources = []
    # loop through cells and save relevant informations
    for cell in cells:
        # check cell metadata
        tags = cell.get('metadata').get('tags', [])
        for tag in tags:
            if tag in selected_tags:
                countTagsFound += 1
                c = {tag: cell.get('source', [])}
                if not c:
                    continue
                cells_sources.append(c)
    if countTagsFound < len(selected_tags):
        logger.error(f'get_notebook_specifics_tags - MISSING TAG in notebook: {raw_url}')
        try:
            # logger.info("HOST" + settings.EMAIL_HOST + " PORT " + settings.EMAIL_PORT)
            body = "One or more than one tag are missing, look at for tags '%s' in the following notebook %s." % (" ".join(selected_tags), raw_url)
            logger.info(body)
            send_mail("Missing tags in notebooks", body, 'jdh.admin@uni.lu', ['jdh.admin@uni.lu;elisabeth.guerard@uni.lu'], fail_silently=False,)
        except Exception as e:  # catch *all* exceptions
            logger.error(f'send_confirmation exception:{e}')
    result = {
        'cells': cells_sources
    }
    return result
