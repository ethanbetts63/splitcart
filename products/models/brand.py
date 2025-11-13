from django.db import models
from scraping.utils.product_scraping_utils.product_normalizer import ProductNormalizer

class ProductBrand(models.Model):
    name = models.CharField(
        max_length=255,
        help_text="The canonical (most common) name for this brand."
    )
    normalized_name = models.CharField(
        max_length=255, 
        unique=True, 
        db_index=True,
        help_text="The normalized version of the brand name, used as the unique key."
    )
    name_variations = models.JSONField(
        default=list, 
        blank=True,
        help_text="A list of all other raw names this brand has been seen as."
    )
    normalized_name_variations = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of normalized names from the name_variations list for faster lookups."
    )
    # Fields from the former BrandPrefix model
    longest_inferred_prefix = models.CharField(max_length=12, null=True, blank=True, db_index=True)
    confirmed_official_prefix = models.CharField(max_length=12, null=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.name and not self.normalized_name:
            self.normalized_name = ProductNormalizer._get_normalized_brand_name(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
