from django.contrib import sitemaps

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['/', '/contact']

    def location(self, item):
        return item

class CategoryPageSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return [
            '/categories/baby/',
            '/categories/bakery-and-deli/',
            '/categories/dairy-and-eggs/',
            '/categories/drinks/',
            '/categories/fruit-and-veg/',
            '/categories/health-beauty-and-supplements/',
            '/categories/home-cleaning-gardening-and-pets/',
            '/categories/international-herbs-and-spices/',
            '/categories/meat-and-seafood/',
            '/categories/pantry/',
            '/categories/snacks-and-sweets/',
        ]

    def location(self, item):
        return item
