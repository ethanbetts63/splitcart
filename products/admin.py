from django.contrib import admin
from .models.product import Product
from .models.price import Price

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    search_fields = ('name', 'brand')

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'price', 'scraped_date')
    autocomplete_fields = ('product', 'store')
    list_filter = ('store', 'scraped_date')
    search_fields = ('product__name', 'store__name')
