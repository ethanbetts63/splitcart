from django.contrib import sitemaps
from django.urls import reverse
from companies.models import PillarPage

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['/']

    def location(self, item):
        return item

class PillarPageSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return PillarPage.objects.all()

    def location(self, obj):
        return f'/pillar-pages/{obj.slug}/'
