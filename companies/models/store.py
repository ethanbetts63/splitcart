from django.db import models
from companies.models.company import Company
from companies.models.division import Division

class Store(models.Model):
    """
    Represents a physical or virtual store where products are sold.
    """

    # Common fields for all stores
    store_name = models.CharField(
        max_length=255,
        help_text="The specific name of the store, e.g., 'IGA Cannington' or 'Coles National'."
        # Coles: name
        # Aldi: name
        # IGA: storeName
        # Woolworths: Name
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='stores',
        help_text="The parent company that owns this store."
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stores',
        help_text="The specific division of the store."
    )
    store_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text="The unique identifier for the store from the company's own system."
        # Coles: id
        # Aldi: id
        # IGA: storeId
        # Woolworths: StoreNo
    )

    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The first line of the store's address."
        # Coles: address.addressLine
        # Aldi: address.address1
        # IGA: address
        # Woolworths: AddressLine1
    )
    suburb = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="The suburb where the store is located."
        # Coles: address.suburb
        # Aldi: address.city
        # IGA: suburb
        # Woolworths: Suburb
    )
    state = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text="The state or territory of the store."
        # Coles: address.state
        # Aldi: address.regionName
        # IGA: state
        # Woolworths: State
    )
    postcode = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="The postcode of the store."
        # Coles: address.postcode
        # Aldi: address.zipCode
        # IGA: postcode
        # Woolworths: Postcode
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="The latitude of the store's location."
        # Coles: position.latitude
        # Aldi: address.latitude
        # IGA: latitude
        # Woolworths: Latitude
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="The longitude of the store's location."
        # Coles: position.longitude
        # Aldi: address.longitude
        # IGA: longitude
        # Woolworths: Longitude
    )

    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the stores details were last updated."
    )
    last_scraped = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time when the store's products were last scraped."
    )
    needs_rescraping = models.BooleanField(
        default=False,
        help_text="Flagged by the system for a high-priority re-scrape."
    )
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time when the store was last scheduled for scraping."
    )

    # Company-specific fields
    
    # IGA
    retailer_store_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="The retailer-specific identifier for the store, if available."
        # IGA: retailerStoreId
    )
    class Meta:
        unique_together = ('company', 'store_id')
        verbose_name = "Store"
        verbose_name_plural = "Stores"

    def __str__(self):
        return f"{self.store_name} ({self.company.name})"
