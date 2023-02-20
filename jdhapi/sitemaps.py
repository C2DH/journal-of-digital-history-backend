from django.contrib.sitemaps import Sitemap
from .models import Article


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'http'

    def items(self):
        return Article.objects.all()

    def lastmod(self, obj):
        return obj.issue.publication_date

    def location(self, obj):
        return "/en/article/%s" % (obj.abstract.pid)
