from jdhapi.utils.copyright import CopyrightJDH
from jdhapi.utils.doi import get_doi, get_publisher_id, get_doi_url_formatted


class ArticleXml:

    """         'authors_concat': CopyrightJDH.getAuthorList(authors),
                'copyright_JDH_url': CopyrightJDH.getCCBYUrl(),
                'copyright_JDH': CopyrightJDH.getCCBYDesc(),
                'title': articleTitle,
                'authors': authors,
                'publisher_id': 'jdh',
                'journal_code': 'jdh',
                'doi_code': 'jdh',
                'issn': '2747-5271',
                'keywords': array_keys,
                'doi': get_doi(article.doi),
                'publisher_id': get_publisher_id(article.doi) """

    def __init__(self, authors_concat):
        self.authors_concat = authors_concat
        # self.doi = get_doi(doi)
        # self.publisher_id = get_publisher_id(doi)

    @property
    def authors_concat(self):
        return self._authors_concat

    @authors_concat.setter
    def authors_concat(self, value):
        print("setting authors_concat")
        self._authors_concat = value

    @classmethod
    def format_properties(cls, authors):
        authors_concat = CopyrightJDH.getAuthorList(authors)
        print(f"inside format_properties {authors}")
        return cls(authors_concat)

