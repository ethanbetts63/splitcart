import time
import json
import requests
from bs4 import BeautifulSoup
from products.models import Product
from api.utils.normalizer import ProductNormalizer

def fetch_and_update_coles_barcodes(command):
    """
    Finds a small batch of Coles products without a barcode and attempts to fetch the GTIN
    from the individual product page for debugging purposes.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Starting Coles Barcode Enrichment Process (Batch of 3) ---"))
    
    # Find the first 3 unique products that have a price from a Coles store and have no barcode.
    products_to_enrich = Product.objects.filter(
        prices__store__company__name__iexact='Coles',
        barcode__isnull=True
    ).distinct()[:3]

    product_count = len(products_to_enrich)
    if not products_to_enrich:
        command.stdout.write("No Coles products missing a barcode were found.")
        return

    command.stdout.write(f"Found {product_count} products to test.")

    session = requests.Session()
    session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
    
    updated_count = 0
    failed_count = 0

    for i, product in enumerate(products_to_enrich):
        command.stdout.write(f"\n--- Processing product {i+1}/{product_count}: {product.name} ---")
        
        price_record = product.prices.filter(store__company__name__iexact='Coles').first()
        sku = price_record.sku if price_record else 'Not Found'

        command.stdout.write(f"  - Brand: {product.brand}")
        command.stdout.write(f"  - Sizes: {product.sizes}")
        command.stdout.write(f"  - SKU: {sku}")
        command.stdout.write(f"  - DB URL: {product.url}")

        if not product.url:
            command.stderr.write(command.style.ERROR("  - Product has no URL. Skipping."))
            failed_count += 1
            continue

        try:
            command.stdout.write(f"  - Fetching URL: {product.url}")
            response = session.get(product.url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            json_element = soup.find('script', {'id': '__NEXT_DATA__'}) 
            if not json_element:
                command.stderr.write(command.style.ERROR("  - Could not find __NEXT_DATA__ script tag on page."))
                failed_count += 1
                continue
            
            data = json.loads(json_element.string)
            gtin = data.get('pageProps', {}).get('product', {}).get('gtin')

            if gtin:
                normalizer = ProductNormalizer({'barcode': gtin, 'sku': sku})
                cleaned_barcode = normalizer.get_cleaned_barcode()

                if cleaned_barcode:
                    command.stdout.write(command.style.SUCCESS(f"  - Found and cleaned barcode: {cleaned_barcode}"))
                    product.barcode = cleaned_barcode
                    product.save(update_fields=['barcode'])
                    updated_count += 1
                else:
                    command.stderr.write(command.style.ERROR(f"  - Found GTIN '{gtin}' but it was deemed invalid after cleaning."))
                    failed_count += 1
            else:
                command.stderr.write(command.style.ERROR("  - Could not find GTIN in the __NEXT_DATA__ JSON."))
                failed_count += 1

            time.sleep(1) # Be respectful to the server

        except Exception as e:
            command.stderr.write(command.style.ERROR(f"  - An error occurred: {e}"))
            failed_count += 1
            continue

    command.stdout.write(command.style.SUCCESS(f"\n--- Enrichment Complete ---"))
    command.stdout.write(f"Successfully updated {updated_count} products.")
    command.stdout.write(f"Failed to find barcodes for {failed_count} products.")
