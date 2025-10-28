from django.db import models
from companies.models import Category

class SuperCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    categories = models.ManyToManyField(Category, related_name='super_categories')

    class Meta:
        verbose_name_plural = "Super Categories"

    def __str__(self):
        return self.name
