from django.db import models

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

    brand = models.ForeignKey(
        'ProductBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Link to the canonical ProductBrand entry."
    )
    # The primary and unique normalized combination of name, brand, and size. 
    normalized_name_brand_size = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="Normalized combination of name, brand, and size for uniqueness."
    )
    # If after being normalized a products normalized_name_brand_size is equal to any of these it is translated to the primary version above.
    # This allows the update orchestrate to recognize a more name variations of a product as the same product.
    normalized_name_brand_size_variations = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of normalized strings for discovered variations."
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
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="The universal barcode (UPC/EAN) of the product."
    )
    company_skus = models.JSONField(
        default=dict,
        blank=True,
        help_text="A dictionary of company names to a list of their SKUs for this product."
    )
    has_no_coles_barcode = models.BooleanField(
        default=False,
        help_text="Set to True if Coles has been scraped and no barcode was found."
    )
    image_url_pairs = models.JSONField(
        default=list,
        blank=True,
        help_text="List of [company_name, image_url] tuples for this product."
    )
    url = models.URLField(max_length=1024, blank=True, null=True)
    
    brand_name_company_pairs = models.JSONField(
        default=list,
        blank=True,
        help_text="List of [raw_brand_name, company_name] tuples for this product."
    )
    substitutes = models.ManyToManyField(
        'self',
        through='ProductSubstitution',
        symmetrical=True,
        blank=True,
        help_text="Other products that can be used as substitutes, ranked by a score."
    )

    def __str__(self):
        size_str = f" ({self.size})" if self.size else ""
        return f"{self.brand} {self.name}{size_str}"
