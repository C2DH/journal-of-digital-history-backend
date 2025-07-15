from django.db import models
import logging

logger = logging.getLogger(__name__)


class CallForPaper(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")
    title = models.CharField(max_length=250)
    folder_name = models.CharField(max_length=250)
    deadline_abstract = models.DateTimeField(blank=True, null=True)
    deadline_article = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
