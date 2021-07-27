from django.db import models
from ..models.author import Author
from ..models.article import Article


class Role(models.Model):
    author = models.ForeignKey('jdhapi.Author', on_delete=models.CASCADE)
    article = models.ForeignKey('jdhapi.Article', on_delete=models.CASCADE)
    order_id = models.IntegerField()

    def __str__(self):
        return str('%s / %s' % (self.article, self.author))
