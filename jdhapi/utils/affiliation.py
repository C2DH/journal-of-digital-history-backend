import logging
from re import I
import pycountry
from jdhseo.utils import get_affiliation
logger = logging.getLogger(__name__)


def get_authors(article_authors, affiliations):
    authors = []
    for author in article_authors:
        for affiliation in affiliations:
            for author_aff in affiliation["authors_link"]:
                if author.lastname == author_aff:
                    # logger.debug(f'author found {author} in affiliation {affiliation["aff_id"]}  ')
                    contrib = {
                        "given_names": author.firstname,
                        "surname": author.lastname,
                        "orcid": author.orcid,
                        "aff_id": affiliation["aff_id"],
                        "aff_pub_id": affiliation["aff_pub_id"]
                    }
        authors.append(contrib)
        # logger.debug(f'authors {authors}')
    return authors


def get_affiliation_json_one(orcid_url, affiliation):
    default_affiliation = {
        "institution": affiliation,
        "city": "NOT FOUND",
        "country": "NOT FOUND",
        "country_name": "NOT FOUND"
    }
    if orcid_url:
        # contact_orcid
        ORCID_URL = "https://orcid.org/"
        orcid = orcid_url.partition(ORCID_URL)[2]
        city_country = get_affiliation(orcid)
        if city_country:
            # if city_country.find('-') != -1:
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
            affiliation = default_affiliation
    else:
        return default_affiliation
    return affiliation


def get_aff_pub_id(publisher_id, aff_id):
    return "j_" + publisher_id.lower() + "_aff_00" + str(aff_id)


def get_affiliation_json(authors, publisher_id):
    affiliations = []
    i = 1
    for author in authors:
        affiliation_one = get_affiliation_json_one(author.orcid, author.affiliation)
        if len(affiliations) == 0:
            affiliation_one["aff_id"] = i
            affiliation_one["authors_link"] = [author.lastname]
            # format j_publisherId_aff_00sup Ex: j_jdh-2021-1006_aff_001
            affiliation_one["aff_pub_id"] = get_aff_pub_id(publisher_id, affiliation_one["aff_id"])
            affiliations.append(affiliation_one)
        else:
            # need to check if already exist
            result = next(
                (item for item in affiliations if item['institution'] == affiliation_one['institution']),
                {}
            )
            if result:
                # need to add author
                result["authors_link"].append(author.lastname)
            else:
                i += 1
                affiliation_one["aff_id"] = i
                affiliation_one["authors_link"] = [author.lastname]
                affiliation_one["aff_pub_id"] = get_aff_pub_id(publisher_id, affiliation_one["aff_id"])
                affiliations.append(affiliation_one)
    # logger.info(f'affiliations: {affiliations}')
    return affiliations


# method to check if affiliation is default_affiliation or not
def is_default_affiliation(affiliations):
    for affiliation in affiliations:
        # if in the affiliation the city is NOT FOUND  or country is NOT FOUND or country_name is NOT FOUND return True
        if affiliation["city"] == "NOT FOUND" or affiliation["country"] == "NOT FOUND" or affiliation["country_name"] == "NOT FOUND":
            return True
    return False
