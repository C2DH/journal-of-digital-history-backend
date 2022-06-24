class CopyrightJDH:

    @staticmethod
    def getCCBYUrl():
        return "http://creativecommons.org/licenses/by/4.0"

    @staticmethod
    def getCCBYDesc():
        return "Creative Commons Attribution 4.0 International License"

    @staticmethod
    def getCCBYNCNDUrl():
        return "http://creativecommons.org/licenses/by-nc-nd/4.0"

    @staticmethod
    def getCCBYNCNDDesc():
        return "Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License"

    # DG rules
    # if nbAuthor == 2  Ex: Sarah Oberbichler and Eva Pfanzelter
    # if nbAuthor > 2   Ex: Petra Heřmánková et al.
    @staticmethod
    def getAuthorList(listAuthors):
        if len(listAuthors) == 1:
            return f"{listAuthors[0]['given_names']} {listAuthors[0]['surname']}"
        if len(listAuthors) == 2:
            return f"{listAuthors[0]['given_names']} {listAuthors[0]['surname']} and {listAuthors[1]['given_names']} {listAuthors[1]['surname']}"
        if len(listAuthors) > 2:
            return f"{listAuthors[0]['given_names']} {listAuthors[0]['surname']} et al."
