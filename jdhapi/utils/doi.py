import re
import logging

logger = logging.getLogger(__name__)


class DOIDG:

    # Example
    # DOI: 10.1515/JDH.2021.1000.R1
    # PublisherId: jdh-2021-1000
    def getPublisherId(doi):
        doi_all = ""
        if doi:
            doi_group = re.split('/', DOIDG.getDoi(doi))
            for index, element in enumerate(doi_group):
                if index == 1:
                    doi_all = element
                    return doi_all
        else:
            return doi_all

    # Example
    # DOI: 10.1515/JDH.2021.1000.R1
    # Doi: 10.1515/jdh-2021-1000
    def getDoi(doi):
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

    # DOI 10.1515/JDH.2021.1006.R1
    # URL https://doi.org/10.1515/JDH-2021-1006
    # stops are replaced by hyphens and the Revision number is removed
    def getDoiUrlDGFormatted(doi):
        doi_all = ""
        if doi:
            DOI_URL = "https://doi.org/"
            doi_all = DOI_URL + DOIDG.getDoi(doi)
            # logger.debug("doi_all" + doi_all)
            # logger.info("rest logger")
            # logger.error("ERROR")
            return doi_all
        else:
            return doi_all
