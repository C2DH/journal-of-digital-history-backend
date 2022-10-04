import re
import logging

logger = logging.getLogger(__name__)


# Example
# DOI: 10.1515/JDH.2021.1000.R1
# Doi: 10.1515/jdh-2021-1000
def get_doi(doi):
    doi_all = ""
    if doi:
        doi_group = re.split('/', doi)
        for index, element in enumerate(doi_group):
            match = re.search('JDH', element)
            if index == 0:
                doi_all = element
            else:
                if match:
                    hyphen = element.replace(".", "-")
                    doi_all = doi_all + "/" + hyphen.rsplit('-', 1)[0]
                    return doi_all
                else:
                    return doi_all
        else:
            return doi_all


# Example
# DOI: 10.1515/JDH.2021.1000.R1
# PublisherId: jdh-2021-1000
def get_publisher_id(doi):
    doi_all = ""
    if doi:
        doi_group = re.split('/', get_doi(doi))
        for index, element in enumerate(doi_group):
            if index == 1:
                doi_all = element
                return doi_all
    else:
        return doi_all


# DOI 10.1515/JDH.2021.1006.R1
# URL https://doi.org/10.1515/JDH-2021-1006
# stops are replaced by hyphens and the Revision number is removed
def get_doi_url_formatted(doi):
    doi_all = ""
    if doi:
        DOI_URL = "https://doi.org/"
        doi_all = DOI_URL + get_doi(doi)
        return doi_all
    else:
        return doi_all


# Variable: {elocation-id}={article-system-creation-date-year} {article-counter-ID}
# http://www.wiki.degruyter.de/production/files/dg_variables_and_id.xhtml#elocation-id
def get_elocation_id(publisher_id):
    # PublisherId: jdh-2021-1000
    elocation_id = publisher_id.replace("-", "").replace("JDH", "")
    return elocation_id


# DOI 10.1515/JDH.2021.1006.R1
# URL https://doi.org/10.1515/JDH-2021-1006?locatt=label:JDHFULL
def get_doi_url_formatted_jdh(doi):
    doi_all = ""
    if doi:
        JDH_PARAM = "?locatt=label:JDHFULL"
        doi_all = get_doi_url_formatted(doi) + JDH_PARAM
        return doi_all
    else:
        return doi_all
