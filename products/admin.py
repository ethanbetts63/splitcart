from django.contrib import admin
from .models.product import Product
from .models.price import Price

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    search_fields = ('name', 'brand')

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'store_group', 'scraped_date', 'source')
    autocomplete_fields = ('product', 'store_group')
    list_filter = ('store_group', 'scraped_date', 'source')
    search_fields = ('product__name', 'store_group__name')
