import re
from jdhapi.utils.copyright import CopyrightJDH
from jdhapi.utils.doi import get_doi, get_publisher_id, get_doi_url_formatted
from jdhapi.utils.affiliation import get_authors, get_affiliation_json
from jdhapi.models import Issue
from django.http import Http404

import logging

logger = logging.getLogger(__name__)


class ArticleXml:

    def __init__(self, article_authors, title, article_doi, keywords, publication_date, copyright, issue_pid):
        self.publisher_id = get_publisher_id(article_doi)
        self.affiliations = get_affiliation_json(article_authors, self.publisher_id)
        self.authors = get_authors(article_authors, self.affiliations)
        self.authors_concat = CopyrightJDH.getAuthorList(self.authors)
        self.title = title
        self.doi = get_doi(article_doi)
        self.publisher_id = get_publisher_id(article_doi)
        self.keywords = keywords
        self.epub = publication_date
        self.ppub = publication_date
        self.cover_date = publication_date
        self.copyright_desc = CopyrightJDH.getCopyrightDesc(copyright)
        self.copyright_url = CopyrightJDH.getCopyrightUrl(copyright)
        # To look at here http://www.wiki.degruyter.de/production/files/dg_xml_guidelines.xhtml#elocation-id
        self.elocation_id = "TO DEFINE"
        # seq reflect the sequence of articles within an issue.
        self.seq = "TO DEFINE"
        try:
            issue = Issue.objects.get(
                pid=issue_pid)
            self.volume = issue.volume
            self.issue = issue.issue
        except Issue.DoesNotExist:
            raise Http404("Issue does not exist")

    @property
    def seq(self):
        return self._seq

    @property
    def elocation_id(self):
        return self._elocation_id

    @property
    def issue(self):
        return self._issue

    @property
    def volume(self):
        return self._volume

    @property
    def copyright_desc(self):
        return self._copyright_desc

    @property
    def copyright_url(self):
        return self._copyright_url

    @property
    def cover_date(self):
        return self._cover_date

    @property
    def ppub(self):
        return self._ppub

    @property
    def epub(self):
        return self._epub

    @property
    def keywords(self):
        return self._keywords

    @property
    def publisher_id(self):
        return self._publisher_id

    @property
    def doi(self):
        return self._doi

    @property
    def authors(self):
        return self._authors

    @property
    def authors_concat(self):
        return self._authors_concat

    @property
    def title(self):
        return self._title

    @copyright_url.setter
    def copyright_url(self, value):
        self._copyright_url = value

    @copyright_desc.setter
    def copyright_desc(self, value):
        self._copyright_desc = value

    @cover_date.setter
    def cover_date(self, value):
        self._cover_date = value

    @ppub.setter
    def ppub(self, value):
        self._ppub = value

    @epub.setter
    def epub(self, value):
        self._epub = value

    @keywords.setter
    def keywords(self, value):
        self._keywords = value

    @doi.setter
    def doi(self, value):
        self._doi = value

    @publisher_id.setter
    def publisher_id(self, value):
        self._publisher_id = value

    @authors.setter
    def authors(self, value):
        self._authors = value

    @title.setter
    def title(self, value):
        self._title = value

    @authors_concat.setter
    def authors_concat(self, value):
        self._authors_concat = value

    @issue.setter
    def issue(self, value):
        self._issue = value

    @volume.setter
    def volume(self, value):
        self._volume = value

    @elocation_id.setter
    def elocation_id(self, value):
        self._elocation_id = value

    @seq.setter
    def seq(self, value):
        self._seq = value
