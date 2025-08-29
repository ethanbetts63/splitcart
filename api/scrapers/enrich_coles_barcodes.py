import time
import json
import requests
from bs4 import BeautifulSoup
from products.models import Product
from api.utils.normalizer import ProductNormalizer

def fetch_and_update_coles_barcodes(command):
    """
    Finds a single Coles product without a barcode and attempts to fetch the GTIN
    from the individual product page for debugging purposes.
    """
    command.stdout.write(command.style.SQL_FIELD("--- Starting Coles Barcode Enrichment Process (Single Product Debug Mode) ---"))
    
    # Find the first unique product that has a price from a Coles store and has no barcode.
    product_to_enrich = Product.objects.filter(
        prices__store__company__name__iexact='Coles',
        barcode__isnull=True
    ).distinct().first()

    if not product_to_enrich:
        command.stdout.write("No Coles products missing a barcode were found.")
        return

    command.stdout.write(f"Found product to test: {product_to_enrich.name}")
    price_record = product_to_enrich.prices.filter(store__company__name__iexact='Coles').first()
    sku = price_record.sku if price_record else 'Not Found'

    command.stdout.write(f"  - Brand: {product_to_enrich.brand}")
    command.stdout.write(f"  - Sizes: {product_to_enrich.sizes}")
    command.stdout.write(f"  - SKU: {sku}")
    command.stdout.write(f"  - DB URL: {product_to_enrich.url}")

    session = requests.Session()
    session.headers.update({"User-Agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)"})
    
    updated = False

    if not product_to_enrich.url:
        command.stderr.write(command.style.ERROR("Product has no URL."))
    else:
        try:
            command.stdout.write(f"Fetching URL: {product_to_enrich.url}")
            response = session.get(product_to_enrich.url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            json_element = soup.find('script', {'id': '__NEXT_DATA__'})
            if not json_element:
                command.stderr.write(command.style.ERROR("Could not find __NEXT_DATA__ script tag on page."))
            else:
                data = json.loads(json_element.string)
                gtin = data.get('pageProps', {}).get('product', {}).get('gtin')

                if gtin:
                    price_record = product_to_enrich.prices.filter(store__company__name__iexact='Coles').first()
                    sku = price_record.store_product_id if price_record else None

                    normalizer = ProductNormalizer({'barcode': gtin, 'sku': sku})
                    cleaned_barcode = normalizer.get_cleaned_barcode()

                    if cleaned_barcode:
                        command.stdout.write(command.style.SUCCESS(f"Found and cleaned barcode: {cleaned_barcode}"))
                        product_to_enrich.barcode = cleaned_barcode
                        product_to_enrich.save(update_fields=['barcode'])
                        updated = True
                    else:
                        command.stderr.write(command.style.ERROR(f"Found GTIN '{gtin}' but it was deemed invalid after cleaning."))
                else:
                    command.stderr.write(command.style.ERROR("Could not find GTIN in the __NEXT_DATA__ JSON."))

        except Exception as e:
            command.stderr.write(command.style.ERROR(f"An error occurred: {e}"))

    command.stdout.write(command.style.SUCCESS(f"--- Enrichment Complete ---"))
    if updated:
        command.stdout.write("Successfully updated 1 product.")
    else:
        command.stdout.write("Failed to update product.")