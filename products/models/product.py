from api.utils.product_normalizer import ProductNormalizer
from django.db import models
from django.db.models import Q

class Product(models.Model):
    """
    Represents a specific product sold at a specific store.
    This record connects the what (the product details) with the where (the store).
    """
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The full name of the product as seen in the store."
    )
    normalized_name = models.CharField(max_length=255, db_index=True, blank=True, help_text="The normalized version of the product name.")
    brand = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="DEPRECATED: The brand of the product as a raw string."
    )
    brand_link = models.ForeignKey(
        'ProductBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Link to the canonical ProductBrand entry."
    )
    size = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The original, raw size string for the product (e.g., 'approx. 300g')."
    )
    
    sizes = models.JSONField(
        default=list,
        help_text="A list of all size-related strings found for the product."
    )
    category = models.ManyToManyField(
        'companies.Category',
        related_name="products",
        help_text="The categories this product belongs to."
    )
    barcode = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        help_text="The universal barcode (UPC/EAN) of the product."
    )
    has_no_coles_barcode = models.BooleanField(
        default=False,
        help_text="Set to True if Coles has been scraped and no barcode was found."
    )
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    url = models.URLField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    allergens = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    health_star_rating = models.FloatField(null=True, blank=True)
    average_user_rating = models.FloatField(null=True, blank=True)
    rating_count = models.IntegerField(null=True, blank=True)
    unit_of_sale = models.CharField(max_length=50, blank=True, null=True)
    dietary_and_lifestyle_tags = models.JSONField(default=list, blank=True)
    is_age_restricted = models.BooleanField(default=False)
    substitutes = models.ManyToManyField(
        'self',
        through='ProductSubstitution',
        symmetrical=True,
        blank=True,
        help_text="Other products that can be used as substitutes, ranked by a score."
    )
    name_variations = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of (name, store) tuples for discovered name variations."
    )
    normalized_name_brand_size_variations = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of normalized strings for discovered variations."
    )

    # TODO: This field should be populated with the normalized versions of the names
    # in `name_variations` to make substitution matching more efficient.
    # This avoids having to re-normalize them on the fly every time.
    normalized_name_variations = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of just the normalized names from the name_variations list."
    )

    normalized_name_brand_size = models.CharField(
        max_length=500,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Normalized combination of name, brand, and size for uniqueness."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['barcode'],
                condition=Q(barcode__isnull=False) & ~Q(barcode=''),
                name='unique_barcode_if_not_null_or_empty'
            ),
            models.UniqueConstraint(
                fields=['normalized_name_brand_size'],
                condition=Q(normalized_name_brand_size__isnull=False),
                name='unique_normalized_name_brand_size'
            )
        ]

    def clean(self):
        super().clean()
        # Use the ProductNormalizer class to generate normalized fields.
        # The normalizer expects a dictionary, so we create one from the model's fields.
        product_data = {
            'name': self.name,
            'brand': self.brand,
            'size': self.size,  # Map model's 'size' field to 'size'
            'barcode': self.barcode,
        }
        normalizer = ProductNormalizer(product_data)
        self.sizes = normalizer.standardized_sizes
        self.normalized_name_brand_size = normalizer.get_normalized_name_brand_size_string()
        self.normalized_name = normalizer.cleaned_name

    def save(self, *args, **kwargs):
        self.clean()  # Ensure data is cleaned and normalized_name_brand_size is set
        super().save(*args, **kwargs)

    def __str__(self):
        sizes_str = ', '.join(self.sizes) if self.sizes else ''
        return f"{self.brand} {self.name} ({sizes_str})"
