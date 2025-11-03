from django.contrib import sitemaps
from django.urls import reverse

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['react_app'] # Assuming 'react_app' is the name of your main app view

    def location(self, item):
        return reverse(item)
