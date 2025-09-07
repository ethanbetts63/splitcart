from django.db import models

class BrandPrefix(models.Model):
    brand = models.OneToOneField(
        'products.ProductBrand',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='prefix_analysis'
    )

    # --- Inferred Data ---
    longest_inferred_prefix = models.CharField(max_length=12, null=True, blank=True, db_index=True)
    shortest_inferred_prefix = models.CharField(max_length=12, null=True, blank=True, db_index=True)

    # --- Verified Data ---
    confirmed_official_prefix = models.CharField(max_length=12, null=True, blank=True, db_index=True)

    def save(self, *args, **kwargs):
        # If a prefix is officially confirmed, it overrides any inferred data.
        if self.confirmed_official_prefix:
            self.longest_inferred_prefix = None
            self.shortest_inferred_prefix = None
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Prefix analysis for {self.brand.name}"