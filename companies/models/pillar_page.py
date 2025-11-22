from django.db import models
from companies.models.primary_category import PrimaryCategory

class PillarPage(models.Model):
    """
    Represents a "super-category" page that groups multiple PrimaryCategory objects
    for SEO and content purposes.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    hero_title = models.CharField(max_length=200)
    introduction_paragraph = models.TextField()
    
    primary_categories = models.ManyToManyField(
        PrimaryCategory,
        related_name='pillar_pages',
        blank=True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
