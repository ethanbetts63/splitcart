from django.db import models
from django.utils.text import slugify

class PrimaryCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    price_comparison_data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Stores price comparison data between companies."
    )

    class Meta:
        verbose_name_plural = "Primary Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
