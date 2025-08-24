from django.contrib import admin
from .models.product import Product
from .models.price import Price

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    search_fields = ('name', 'brand')

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'store', 'price', 'is_on_special', 'scraped_at')
    autocomplete_fields = ('product', 'store')