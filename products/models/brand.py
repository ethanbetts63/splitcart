from django.db import models
from api.utils.product_normalizer import ProductNormalizer

class ProductBrand(models.Model):
    name = models.CharField(max_length=255, unique=True)
    normalized_name = models.CharField(max_length=255, unique=True, db_index=True)
    name_variations = models.JSONField(default=list, blank=True)
    is_store_brand = models.BooleanField(default=False)

    # Link to the top-level corporate owner.
    parent_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if self.name:
            # The normalizer expects a dictionary.
            # Pass brand name and an empty product name for context for brand rules.
            product_data = {'brand': self.name, 'name': ''}
            normalizer = ProductNormalizer(product_data)
            self.normalized_name = normalizer.cleaned_brand
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name