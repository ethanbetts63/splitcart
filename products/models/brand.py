from django.db import models

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

    def __str__(self):
        return self.name
