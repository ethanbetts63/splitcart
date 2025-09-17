from django.core.management.base import BaseCommand
from products.models import Product, ProductBrand

class Command(BaseCommand):
    help = 'Inspects the top 50 brands by product count and shows their prefix details.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Inspecting Top 50 Brands by Product Count ---"))

        all_brands = ProductBrand.objects.all()
        brand_counts = []

        self.stdout.write("Calculating product counts for all brands...")
        for brand in all_brands:
            count = Product.objects.filter(brand=brand).count()
            brand_counts.append({'brand': brand, 'count': count})
        
        sorted_brands = sorted(brand_counts, key=lambda x: x['count'], reverse=True)
        top_50_brands = sorted_brands[:50]

        self.stdout.write(self.style.SUCCESS("\n--- Top 50 Brands ---"))
        for i, brand_info in enumerate(top_50_brands):
            brand = brand_info['brand']
            count = brand_info['count']
            
            prefix_details = f"Confirmed Prefix: '{brand.confirmed_official_prefix or 'N/A'}'"

            self.stdout.write(
                f"{i+1}. Brand: '{brand.name}' (ID: {brand.id})\n"
                f"   - Product Count: {count}\n"
                f"   - Prefix Details: {prefix_details}\n"
                f"--------------------------------------------------"
            )
