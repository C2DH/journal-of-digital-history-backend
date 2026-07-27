from django.contrib.sitemaps import Sitemap
from jdhapi.models.article import Article


# Each article page
class ArticlesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Article.objects.all()

    def location(self, obj):
        # Return URL path for each article
        return f"/article/{obj.abstract.pid}"   
    
    def lastmod(self, obj):
        return obj.publication_date

        
# Static page (eg. '/' or '/articles')
class StaticSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return ["home", "articles", "submit", "guidelines", "preview", "about", "review", "faq", "releases", "terms"]

    def location(self, item):
        if item == "home":
            return "/"
        elif item == "articles":
            return "/articles"
        elif item == "submit":
            return "/submit"
        elif item == "guidelines":
            return "/guidelines"
        elif item == "preview":
            return "/notebook-viewer-form"
        elif item == "about":
            return "/about"
        elif item == "review":
            return "/review-policy"
        elif item == "faq":
            return "/faq"
        elif item == "releases":
            return "/release-notes"
        elif "terms":
            return "/terms"
            