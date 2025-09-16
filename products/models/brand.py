from django.db import models
from api.utils.product_normalizer import ProductNormalizer

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
    is_store_brand = models.BooleanField(default=False)

    # Link to the top-level corporate owner.
    parent_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if self.name and not self.normalized_name:
            self.normalized_name = ProductNormalizer._clean_value(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
