from django.db import models
from .company import Company
from .division import Division

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
    is_active = models.BooleanField(
        default=True,
        help_text="True if the store is currently being scraped."
    )
    is_online_shopable = models.BooleanField(
        default=False,
        help_text="True if the store has a functioning online shop that can be scraped."
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="The contact phone number for the store."
        # Coles: phone
        # Aldi: publicPhoneNumber
        # IGA: phone
        # Woolworths: Phone
    )
    address_line_1 = models.CharField(
        max_length=255,
        blank=True,
        help_text="The first line of the store's address."
        # Coles: address.addressLine
        # Aldi: address.address1
        # IGA: address
        # Woolworths: AddressLine1
    )
    address_line_2 = models.CharField(
        max_length=255,
        blank=True,
        help_text="The second line of the store's address."
        # Aldi: address.address2
        # Woolworths: AddressLine2
    )
    suburb = models.CharField(
        max_length=100,
        blank=True,
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
    trading_hours = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing the store's trading hours."
        # IGA: hours and hoursDay
        # Woolworths: TradingHours
    )
    facilities = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing a list of store facilities."
        # Aldi: facilities
        # Woolworths: Facilities
    )
    is_trading = models.BooleanField(
        null=True,
        blank=True,
        help_text="Indicates if the store is currently trading."
        # Coles: isTrading
        # Aldi: isOpenNow
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="The date and time when the stores details were last updated."
    )
    last_scraped_products = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time when the store's products were last scraped."
    )

    # Company-specific fields
    
    # IGA
    retailer_store_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="The retailer-specific identifier for the store, if available."
        # IGA: retailerStoreId
    )
    email = models.EmailField(
        blank=True,
        help_text="The contact email for the store."
        # IGA: email
    )
    online_shop_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="The URL for the store's online shopping portal."
        # IGA: onlineShopUrl
    )
    store_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="The URL for the store's website."
        # IGA: storeUrl
    )
    ecommerce_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="The URL for the store's e-commerce platform."
        # IGA: ecommerceUrl
    )
    record_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="The unique identifier for the store record from the IGA system."
        # IGA: id
    )
    status = models.CharField(
        max_length=50,
        blank=True,
        help_text="The status of the store (e.g., 'Active')."
        # IGA: status
    )
    store_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="The type of the store (e.g., 'Regular')."
        # IGA: type
    )
    site_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="The ID of the site from the IGA system."
        # IGA: siteId
    )
    
    shopping_modes = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing a list of available shopping modes."
        # IGA: shoppingModes
    )

    # Aldi
    available_customer_service_types = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing a list of available customer service types."
        # Aldi: availableCustomerServiceTypes
    )
    alcohol_availability = models.JSONField(
        null=True,
        blank=True,
        help_text="A JSON object storing a list of available alcohol types."
        # Aldi: alcoholAvailability
    )

    class Meta:
        unique_together = ('company', 'store_id')
        verbose_name = "Store"
        verbose_name_plural = "Stores"

    def __str__(self):
        return f"{self.name} ({self.company.name})"
