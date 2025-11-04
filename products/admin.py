from django.contrib import admin
from .models.product import Product
from .models.price import Price
from .models.price_record import PriceRecord

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    search_fields = ('name', 'brand')

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('get_product', 'store', 'get_scraped_date', 'source')
    autocomplete_fields = ('price_record', 'store')
    list_filter = ('store', 'price_record__scraped_date', 'source')
    search_fields = ('price_record__product__name', 'store__store_name')

    def get_product(self, obj):
        return obj.price_record.product
    get_product.admin_order_field = 'price_record__product'

    def get_scraped_date(self, obj):
        return obj.price_record.scraped_date
    get_scraped_date.admin_order_field = 'price_record__scraped_date'
    get_scraped_date.short_description = 'Scraped Date'

@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'was_price', 'is_on_special')
    autocomplete_fields = ('product',)
    search_fields = ('product__name',)
