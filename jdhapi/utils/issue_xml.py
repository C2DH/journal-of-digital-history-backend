from django.http import Http404
from jdhapi.utils.doi import get_doi, get_publisher_id, get_elocation_id
from jdhapi.utils.publication_date import get_order_publication
from jdhapi.models import Issue
from jdhapi.utils.publication_date import check_if_editorial
from jdhapi.utils.doi import get_doi

import logging
from jdhapi.models import Article

logger = logging.getLogger(__name__)


class IssueXml:


    def __init__(
        self,
        issue_pid,
    ):


        try:
            issue = Issue.objects.get(pid=issue_pid)
            self.volume = issue.volume
            self.issue = issue.issue
            self.issue_date = issue.publication_date
            # jdh.[issue_date_year].[volume].issue-[issue]
            self.publisher_id = f"jdh.{self.issue_date.year}.{self.volume}.issue-{self.issue}"
            self.articles_dois = self.fetch_articles_dois(issue_pid)
        except Issue.DoesNotExist:
            raise Http404("Issue does not exist")
        
    def fetch_articles_dois(self, issue_pid):
        articles = Article.objects.filter(
            issue__pid=issue_pid,
            status=Article.Status.PUBLISHED
        ).order_by('-publication_date')
        try:
            # Separate editorials and non-editorials
            editorials = [article for article in articles if check_if_editorial(article.abstract.pid)]
            non_editorials = [article for article in articles if not check_if_editorial(article.abstract.pid)]
            # Put editorials first
            ordered_articles = editorials + non_editorials
            return [get_doi(article.doi) for article in ordered_articles]
        except Exception as e:
            logger.error(f"Error fetching articles DOIs: {e}")
            return []
             
    @property
    def publisher_id(self):
        return self._publisher_id

    @publisher_id.setter
    def publisher_id(self, value):
        self._publisher_id = value

    @property
    def issue(self):
        return self._issue

    @property
    def volume(self):
        return self._volume
    
    @property
    def issue_date(self):
        return self._issue_date

    @issue.setter
    def issue(self, value):
        self._issue = value

    @volume.setter
    def volume(self, value):
        self._volume = value


    @issue_date.setter
    def issue_date(self, value):
        self._issue_date = value
