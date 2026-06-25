from django.db import models

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
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
