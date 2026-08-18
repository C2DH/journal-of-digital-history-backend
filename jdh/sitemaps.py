from django.contrib.sitemaps import Sitemap
from jdhapi.models import Article, CallForPaper


# Each article page
class ArticlesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Article.objects.all()

    def location(self, obj):
        # Return URL path for each article
        return f"/en/article/{obj.abstract.pid}"

    def lastmod(self, obj):
        return obj.publication_date


# Each Callforpaper page
class CallforpaperSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return CallForPaper.objects.all()

    def location(self, obj):
        # Return URL path for each cfp
        return f"/en/cfp/{obj.folder_name}"

    def lastmod(self, obj):
        return obj.deadline_article


# Static page (eg. '/' or '/articles')
class StaticSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return [
            "home",
            "articles",
            "submit",
            "guidelines",
            "preview",
            "about",
            "review",
            "faq",
            "releases",
            "terms",
        ]

    def location(self, item):
        if item == "home":
            return "/en"
        elif item == "articles":
            return "/en/articles"
        elif item == "submit":
            return "/en/submit"
        elif item == "guidelines":
            return "/en/guidelines"
        elif item == "preview":
            return "/en/notebook-viewer-form"
        elif item == "about":
            return "/en/about"
        elif item == "review":
            return "/en/review-policy"
        elif item == "faq":
            return "/en/faq"
        elif item == "releases":
            return "/en/release-notes"
        elif "terms":
            return "/en/terms"
