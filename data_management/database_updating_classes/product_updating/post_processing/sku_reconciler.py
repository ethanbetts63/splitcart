from collections import defaultdict
from django.db.models import Count
from companies.models import Company
from products.models import Product, Price
from ..product_enricher import ProductEnricher

class SkuReconciler:
    def __init__(self, command, unit_of_work):
        self.command = command
        self.unit_of_work = unit_of_work
        self.products_to_delete = []
        self.prices_to_delete_ids = []

    def run(self):
        """
        Main entry point for the SKU reconciliation process.
        """
        self.command.stdout.write(self.style.SUCCESS("--- Starting SKU Reconciliation Stage ---"))
        companies = Company.objects.all()
        for company in companies:
            self._reconcile_company(company)
        self.command.stdout.write(self.style.SUCCESS("--- SKU Reconciliation Stage Finished ---"))

    def _reconcile_company(self, company):
        """
        Performs SKU reconciliation for a single company.
        """
        company_name_lower = company.name.lower()
        self.command.stdout.write(self.style.HTTP_INFO(f"\nAnalyzing SKUs for: {company.name}"))

        # 1. Get all products for the company and build the SKU-to-product map
        product_pks = Price.objects.filter(store__company=company).values_list('product_id', flat=True).distinct()
        products = Product.objects.filter(pk__in=product_pks).prefetch_related('prices')
        
        sku_to_products = defaultdict(list)
        for product in products:
            sku_list = product.company_skus.get(company_name_lower, [])
            for sku in sku_list:
                sku_to_products[sku].append(product)

        # 2. Find and process groups of products sharing a SKU
        conflicting_groups = {sku: prods for sku, prods in sku_to_products.items() if len(prods) > 1}
        
        if not conflicting_groups:
            self.command.stdout.write("  No SKU conflicts found to reconcile.")
            return

        self.command.stdout.write(f"  Found {len(conflicting_groups)} SKUs mapping to multiple products. Analyzing for merging...")
        
        for sku, group in conflicting_groups.items():
            # 3. Perform barcode safety check
            barcodes_found = {p.barcode for p in group if p.barcode}
            if len(barcodes_found) > 1:
                self.command.stdout.write(self.style.WARNING(f"  - Skipping SKU '{sku}': Found multiple distinct barcodes {barcodes_found}. Manual review required."))
                continue

            # 4. If safe, merge the group
            self._merge_product_group(group, sku)

    def _merge_product_group(self, group, sku):
        """
        Merges a group of products that share a safe SKU.
        """
        # 5. Choose the canonical product
        canonical_product = self._choose_canonical(group)
        duplicate_products = [p for p in group if p.id != canonical_product.id]

        self.command.stdout.write(f"  - Merging {len(duplicate_products)} duplicates into Product PK {canonical_product.pk} for SKU '{sku}'.")

        for duplicate in duplicate_products:
            # 6. Enrich canonical product with data from the duplicate
            ProductEnricher.enrich_from_product(canonical_product, duplicate)
            
            # 7. Move prices to the canonical product via the UnitOfWork
            for price in duplicate.prices.all():
                price_details = {
                    'price_current': price.price, 'was_price': price.was_price,
                    'unit_price': price.unit_price, 'unit_of_measure': price.unit_of_measure,
                    'per_unit_price_string': price.per_unit_price_string,
                    'is_on_special': price.is_on_special, 'price_hash': price.price_hash,
                }
                metadata = {'scraped_date': price.scraped_date.strftime('%Y-%m-%d')}
                self.unit_of_work.add_price(canonical_product, price.store, price_details, metadata)
                self.prices_to_delete_ids.append(price.id)

            # 8. Stage the duplicate product for deletion
            self.products_to_delete.append(duplicate)

    def _choose_canonical(self, group):
        """
        Selects the best canonical product from a group based on a hierarchy of rules.
        """
        # Rule 1: Prefer product with a barcode
        with_barcode = [p for p in group if p.barcode]
        if len(with_barcode) == 1:
            return with_barcode[0]
        
        # Rule 2: Prefer product with the most price records (as a proxy for history/completeness)
        # This uses the prefetched 'prices' related manager
        group.sort(key=lambda p: p.prices.count(), reverse=True)
        
        # Check for ties in the top spot
        if len(group) > 1 and group[0].prices.count() > group[1].prices.count():
            return group[0]

        # Rule 3: As a final tie-breaker, prefer the one with the lowest PK (oldest)
        group.sort(key=lambda p: p.pk)
        return group[0]
