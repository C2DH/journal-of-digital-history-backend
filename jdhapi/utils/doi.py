import re


class DOIDG:

    # DOI 10.1515/JDH.2021.1006.R1
    # URL https://doi.org/10.1515/JDH-2021-1006
    # stops are replaced by hyphens and the Revision number is removed,
    def getDoiUrlDGFormatted(doi):
        doi_all = ""
        if doi:
            DOI_URL = "https://doi.org/"
            doi_group = re.split('/', doi)
            for index, element in enumerate(doi_group):
                match = re.search('JDH', element)
                if index == 0:
                    doi_all = DOI_URL + element
                else:
                    if match:
                        hyphen = element.replace(".", "-")
                        doi_all = doi_all + "/" + hyphen.rsplit('-', 1)[0]
                        return doi_all
                    else:
                        return doi_all
        else:
            return doi_all
