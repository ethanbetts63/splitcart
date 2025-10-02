
import os
import json
from django.core.management.base import BaseCommand
from products.models import Product, Price
from companies.models import Store

class Command(BaseCommand):
    help = 'Fixes the image URLs for Coles products in the database.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to fix Coles image URLs in the database...'))

        coles_stores = Store.objects.filter(company__name='Coles')
        coles_prices = Price.objects.filter(store__in=coles_stores)

        updated_products = 0
        for price in coles_prices:
            try:
                # The Price model has a ForeignKey to PriceRecord, which has a ForeignKey to Product
                # However, the provided model definitions don't show a direct link from Price to Product.
                # I will assume there is a way to get the product from the price, for example through a related name or another model.
                # Based on the price model, it seems to be price.price_record.product
                
                if not hasattr(price, 'price_record') or not hasattr(price.price_record, 'product'):
                    continue

                product = price.price_record.product
                sku = price.sku

                if not sku:
                    continue

                first_digit = str(sku)[0]
                new_url = f"https://productimages.coles.com.au/productimages/{first_digit}/{sku}.jpg"

                updated = False
                if not product.image_url_pairs:
                    product.image_url_pairs = []
                    
                for i, pair in enumerate(product.image_url_pairs):
                    if pair[0] == 'Coles':
                        if pair[1] != new_url:
                            product.image_url_pairs[i][1] = new_url
                            updated = True
                        else:
                            # URL is already correct
                            updated = False # To avoid saving again
                        break
                else: # No 'Coles' entry found
                    product.image_url_pairs.append(['Coles', new_url])
                    updated = True

                if updated:
                    product.save()
                    updated_products += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated image URL for product: {product.name} (SKU: {sku})"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to process price record {price.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f'Finished fixing Coles image URLs. {updated_products} products were updated.'))
