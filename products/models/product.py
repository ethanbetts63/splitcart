from django.db import models
from django.db.models import Q
import re
from companies.models.category import Category

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
    brand = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="The brand of the product, e.g., 'Coles', 'Coca-Cola'."
    )
    
    sizes = models.JSONField(
        default=list,
        help_text="A list of all size-related strings found for the product."
    )
    category = models.ManyToManyField(
        Category,
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
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    url = models.URLField(max_length=1024, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)
    allergens = models.TextField(blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)
    substitute_goods = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text="Optional: Other products that can be used as substitutes."
    )
    size_variants = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        help_text="Products that are the same item but in a different size."
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

    def _clean_value(self, value):
        if value is None:
            return ''
        # Split into words, sort them, and join back
        words = sorted(str(value).lower().split())
        sorted_string = ' '.join(words)
        # Remove non-alphanumeric characters and spaces
        cleaned_value = re.sub(r'[^a-z0-9]', '', sorted_string)
        return cleaned_value

    def _extract_sizes(self, text):
        if not text:
            return []

        sizes = set()
        # We work on a modifiable copy of the text, lowercased for consistency
        processed_text = text.lower()

        # Dictionary to map all unit variations to a standard form (e.g., 'grams' -> 'g')
        units = {
            'g': ['g', 'gram', 'grams'],
            'kg': ['kg', 'kilogram', 'kilograms'],
            'ml': ['ml', 'millilitre', 'millilitres'],
            'l': ['l', 'litre', 'litres'],
            'pk': ['pk', 'pack', 'packs'],
            'ea': ['each', 'ea'],
        }
        unit_map = {variation: standard for standard, variations in units.items() for variation in variations}
        all_unit_variations = list(unit_map.keys())

        # --- Patterns are ordered from most specific to most general ---

        # 1. Ranges (e.g., "10-15kg", "400-500g")
        range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(range_pattern, processed_text):
            unit = unit_map[match.group(3)]
            sizes.add(f"{match.group(1)}{unit}")
            sizes.add(f"{match.group(2)}{unit}")
        processed_text = re.sub(range_pattern, '', processed_text)

        # 2. Multipacks (e.g., "4x250ml", "6 x 75g")
        multipack_pattern_1 = r'(\d+)\s*[xX]\s*(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(multipack_pattern_1, processed_text):
            unit = unit_map[match.group(3)]
            sizes.add(f"{match.group(1)}pk")
            sizes.add(f"{match.group(2)}{unit}")
        processed_text = re.sub(multipack_pattern_1, '', processed_text)

        # 3. Multipacks - reversed (e.g., "250ml x 4", "75g x 6")
        multipack_pattern_2 = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\s*[xX]\s*(\d+)'
        for match in re.finditer(multipack_pattern_2, processed_text):
            unit = unit_map[match.group(2)]
            sizes.add(f"{match.group(1)}{unit}")
            sizes.add(f"{match.group(3)}pk")
        processed_text = re.sub(multipack_pattern_2, '', processed_text)

        # 4. Standard, simple sizes (e.g., "500g", "5 pack") - the fallback
        standard_pattern = r'(\d+\.?\d*)\s*(' + '|'.join(all_unit_variations) + r')\b'
        for match in re.finditer(standard_pattern, processed_text):
            unit = unit_map[match.group(2)]
            sizes.add(f"{match.group(1)}{unit}")

        return list(sizes)

    def clean(self):
        super().clean()
        # Extract sizes from name and brand
        name_sizes = self._extract_sizes(self.name)
        brand_sizes = self._extract_sizes(self.brand)

        # Combine with existing sizes, ensure uniqueness, and sort
        all_sizes = set(self.sizes)
        all_sizes.update(name_sizes)
        all_sizes.update(brand_sizes)
        self.sizes = sorted(list(all_sizes))

    def _get_cleaned_name(self):
        name = self.name
        # Remove brand from name
        if self.brand and self.brand.lower() in name.lower():
            name = re.sub(r'\b' + re.escape(self.brand) + r'\b', '', name, flags=re.IGNORECASE).strip()
        
        # Remove all identified size strings from the name
        if self.sizes:
            for s in self.sizes:
                # Also remove the exact size string, which might be in formats like "6x100g"
                name = name.replace(s, '').strip()

        # A more general regex to remove any remaining size-like patterns
        units = ['g', 'gram', 'grams', 'kg', 'kilogram', 'kilograms', 'ml', 'millilitre', 'millilitres', 'l', 'litre', 'litres', 'pk', 'pack', 'each', 'ea']
        size_pattern = r'\b\d+\.?\d*\s*(' + '|'.join(units) + r')s?\b' # added 's?' to handle pluralization
        name = re.sub(size_pattern, '', name, flags=re.IGNORECASE)
        
        # Clean up extra spaces that might be left after removal
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def save(self, *args, **kwargs):
        self.clean()  # Ensure data is cleaned before saving
        cleaned_name = self._get_cleaned_name()

        # Generate normalized_name_brand_size before saving
        self.normalized_name_brand_size = self._clean_value(cleaned_name) + \
                                          self._clean_value(self.brand) + \
                                          self._clean_value(" ".join(self.sizes) if self.sizes else "")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand} {self.name} ({self.size})"