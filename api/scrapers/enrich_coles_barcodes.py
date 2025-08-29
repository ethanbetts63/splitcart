import time
import json
import requests
from bs4 import BeautifulSoup
from products.models import Product
from api.utils.normalizer import ProductNormalizer

def fetch_and_update_coles_barcodes(command):
    """
    Finds Coles products without a barcode and attempts to fetch the GTIN
    from the individual product page.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Starting Coles Barcode Enrichment Process ---"))
    
    # Find all unique products that have a price from a Coles store and have no barcode.
    products_to_enrich = Product.objects.filter(
        prices__store__company__name__iexact='Coles',
        barcode__isnull=True
    ).distinct()

    product_count = products_to_enrich.count()
    command.stdout.write(f"Found {product_count} Coles products missing a barcode.")

    if product_count == 0:
        return

    session = requests.Session()
    session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
    
    updated_count = 0
    failed_count = 0

    for i, product in enumerate(products_to_enrich):
        command.stdout.write(f"\rProcessing product {i+1}/{product_count}: {product.name[:50]}", ending='')

        if not product.url:
            failed_count += 1
            continue

        try:
            response = session.get(product.url, timeout=20)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            json_element = soup.find('script', {'id': '__NEXT_DATA__'}) # Corrected: removed unnecessary escaping for single quotes
            if not json_element:
                failed_count += 1
                continue

            data = json.loads(json_element.string)
            gtin = data.get('pageProps', {}).get('product', {}).get('gtin')

            if gtin:
                # Use the ProductNormalizer to clean the barcode
                # We need the SKU for the cleaning logic, get it from the first available price record
                price_record = product.prices.filter(store__company__name__iexact='Coles').first()
                sku = price_record.store_product_id if price_record else None

                normalizer = ProductNormalizer({'barcode': gtin, 'product_id_store': sku})
                cleaned_barcode = normalizer.get_cleaned_barcode()

                if cleaned_barcode:
                    product.barcode = cleaned_barcode
                    product.save(update_fields=['barcode'])
                    updated_count += 1
            else:
                failed_count += 1

            # Be respectful to the server
            time.sleep(1)

        except Exception:
            failed_count += 1
            continue

    command.stdout.write("\n") # Newline after progress bar
    command.stdout.write(command.style.SUCCESS("--- Enrichment Complete ---"))
    command.stdout.write(f"Successfully updated {updated_count} products.")
    command.stdout.write(f"Failed to find barcodes for {failed_count} products.")
