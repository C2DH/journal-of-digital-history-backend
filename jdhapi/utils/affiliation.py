import logging
from re import I
import pycountry
from jdhseo.utils import get_affiliation
logger = logging.getLogger(__name__)


def get_authors(article_authors):
    authors = []
    for author in article_authors:
        contrib = {
            "given_names": author.firstname,
            "surname": author.lastname,
            "orcid": author.orcid
        }
        authors.append(contrib)
        logger.debug(f'authors {authors}')
    return authors


def get_affiliation_json_one(orcid_url, affiliation):
    # contact_orcid
    ORCID_URL = "https://orcid.org/"
    orcid = orcid_url.partition(ORCID_URL)[2]
    city_country = get_affiliation(orcid)
    if city_country.find('-') != -1:
        city = city_country.partition('-')[0].strip()
        country = city_country.partition('-')[2].strip()
        country_name = pycountry.countries.get(alpha_2=country).name
        affiliation = {
            "institution": affiliation,
            "city": city,
            "country": country,
            "country_name": country_name
        }
    else:
        affiliation = {
            "institution": affiliation,
            "city": "NOT FOUND",
            "country": "NOT FOUND",
            "country_name": "NOT FOUND"
        }
    return affiliation


def get_affiliation_json(authors):
    affiliations = []
    i = 1
    for author in authors:
        affiliation_one = get_affiliation_json_one(author.orcid, author.affiliation)
        if len(affiliations) == 0:
            affiliation_one["aff_id"] = i
            affiliations.append(affiliation_one)
        else:
            # need to check if already exist
            result = next(
                (item for item in affiliations if item['institution'] == affiliation_one['institution']),
                {}
            )
            if not result:
                i += 1
                affiliation_one["aff_id"] = i
                logger.info(f'new affiliation: {affiliation_one["institution"]}')
                affiliations.append(affiliation_one)
    logger.info(f'affiliations: {affiliations}')
    return affiliations


"""             for item in affiliations:
                if affiliation_one["institution"] == item["institution"] in item.values():
                    logger.info(f'already exist: {item["institution"]}') """


"""     authors_full = []
    for author in authors:
        contrib = {
            "given_names": author.firstname,
            "surname": author.lastname,
            "orcid": author.orcid
        }
        get_affiliation_json_one(author.orcid)
        authors_full.append(contrib)
        logger.debug(f'authors {authors_full}') """