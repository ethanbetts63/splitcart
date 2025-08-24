from django.contrib import admin
from .models.company import Company
from .models.division import Division
from .models.store import Store
from .models.category import Category

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'company', 'suburb', 'state')
    search_fields = ('store_name', 'suburb')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    search_fields = ('name',)