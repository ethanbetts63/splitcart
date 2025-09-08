from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from companies.models.company import Company
from companies.models.store import Store
from api.scrapers.product_scraper_woolworths import ProductScraperWoolworths
from api.scrapers.product_scraper_coles import ColesScraper as ProductScraperColes
from api.scrapers.product_scraper_aldi import ProductScraperAldi
from api.scrapers.product_scraper_iga import IgaScraper as ProductScraperIga
from api.utils.scraper_utils.get_woolworths_categories import get_woolworths_categories
from api.utils.scraper_utils.get_coles_categories import get_coles_categories
from api.scrapers.gs1_company_scraper import Gs1CompanyScraper
from products.models import BrandPrefix, Product, ProductBrand
import time
import os

class Command(BaseCommand):
    help = 'Runs the scrapers for the specified companies.'

    def add_arguments(self, parser):
        parser.add_argument('--woolworths', action='store_true', help='Run the Woolworths scraper.')
        parser.add_argument('--coles', action='store_true', help='Run the Coles scraper.')
        parser.add_argument('--aldi', action='store_true', help='Run the Aldi scraper.')
        parser.add_argument('--iga', action='store_true', help='Run the IGA scraper.')
        parser.add_argument('--gs1', action='store_true', help='Run the GS1 company prefix scraper test.')
        parser.add_argument('--batch-size', type=int, default=100, help='The number of stores to scrape per run.')

    def handle(self, *args, **options):
        run_all = not any(options[company] for company in ['woolworths', 'coles', 'aldi', 'iga', 'gs1'])
        batch_size = options['batch_size']
        if options['woolworths'] or run_all:
            try:
                woolworths_company = Company.objects.get(name="Woolworths")
                stores = Store.objects.filter(company=woolworths_company, is_active=True, division__name__iexact='supermarkets')
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                categories = get_woolworths_categories(self)
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Woolworths categories. Aborting Woolworths scrape.'))
                else:
                    for store in stores_to_scrape:
                        scraper = ProductScraperWoolworths(
                            command=self,
                            company=woolworths_company.name,
                            store_id=store.store_id,
                            store_name=store.store_name,
                            state=store.state,
                            categories_to_fetch=categories
                        )
                        scraper.run()
                        store.last_scraped_products = timezone.now()
                        store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Woolworths" not found.'))

        if options['coles'] or run_all:
            try:
                coles_company = Company.objects.get(name="Coles")
                stores = Store.objects.filter(company=coles_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                categories = get_coles_categories()
                if not categories:
                    self.stdout.write(self.style.ERROR('Could not fetch Coles categories. Aborting Coles scrape.'))
                else:
                    for store in stores_to_scrape:
                        scraper = ProductScraperColes(
                            command=self,
                            company=coles_company.name,
                            store_id=store.store_id,
                            store_name=store.store_name,
                            state=store.state,
                            categories_to_fetch=categories
                        )
                        scraper.run()
                        store.last_scraped_products = timezone.now()
                        store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Coles" not found.'))

        if options['aldi'] or run_all:
            try:
                aldi_company = Company.objects.get(name="Aldi")
                stores = Store.objects.filter(company=aldi_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                for store in stores_to_scrape:
                    scraper = ProductScraperAldi(
                        command=self,
                        company=aldi_company.name,
                        store_id=store.store_id,
                        store_name=store.store_name,
                        state=store.state
                    )
                    scraper.run()
                    store.last_scraped_products = timezone.now()
                    store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Aldi" not found.'))

        if options['iga'] or run_all:
            try:
                iga_company = Company.objects.get(name="Iga")
                stores = Store.objects.filter(company=iga_company, is_active=True)
                stores_to_scrape = stores.order_by('last_scraped_products')[:batch_size]
                for store in stores_to_scrape:
                    scraper = ProductScraperIga(
                        command=self,
                        company=iga_company.name,
                        store_id=store.store_id,
                        retailer_store_id=store.retailer_store_id,
                        store_name=store.store_name,
                        state=store.state
                    )
                    scraper.run()
                    store.last_scraped_products = timezone.now()
                    store.save()
            except Company.DoesNotExist:
                self.stdout.write(self.style.ERROR('Company "Iga" not found.'))

        self.stdout.write(self.style.SUCCESS('Scraping complete.'))

        if options['gs1']:
            self.stdout.write(self.style.SUCCESS('--- Running GS1 Strategic Scraper to Inbox ---'))
            
            # Setup inbox file
            inbox_dir = os.path.join(settings.BASE_DIR, 'api', 'data', 'prefix_inbox')
            os.makedirs(inbox_dir, exist_ok=True)
            timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_file = os.path.join(inbox_dir, f'gs1_results_{timestamp}.jsonl')
            self.stdout.write(f"Saving results to: {output_file}")

            scraper = Gs1CompanyScraper(self)
            successful_scrapes = 0
            brands_attempted_this_run = set()

            # 1. Get all ProductBrands and their counts, sort them once.
            self.stdout.write("Calculating product counts for all brands to determine priority...")
            all_brands = ProductBrand.objects.all()
            brand_counts = []
            for brand in all_brands:
                count = Product.objects.filter(brand=brand.name).count()
                if count > 0:
                    brand_counts.append({'brand': brand, 'count': count})
            
            sorted_brands = sorted(brand_counts, key=lambda x: x['count'], reverse=True)
            self.stdout.write(f"Prioritized a list of {len(sorted_brands)} brands.")

            # 2. Main scraping loop
            for i in range(2):
                if successful_scrapes >= 30: break

                # 3. Find the next target from the sorted list
                target_brand = None
                for brand_info in sorted_brands:
                    brand_obj = brand_info['brand']
                    if brand_obj.id in brands_attempted_this_run:
                        continue

                    try:
                        prefix_analysis = brand_obj.prefix_analysis
                        if prefix_analysis.confirmed_official_prefix:
                            brands_attempted_this_run.add(brand_obj.id)
                            continue
                    except BrandPrefix.DoesNotExist:
                        pass
                    
                    target_brand = brand_obj
                    break

                if not target_brand:
                    self.stdout.write(self.style.SUCCESS("No more unverified brands to scrape. Ending run."))
                    break

                # 4. Process the target brand
                brands_attempted_this_run.add(target_brand.id)
                self.stdout.write(f"--- Scrape Attempt {i + 1}/30 ---")
                self.stdout.write(f"Selected brand: {target_brand.name}")

                product_with_barcode = Product.objects.filter(
                    brand=target_brand.name
                ).exclude(barcode__isnull=True).exclude(barcode__exact='').first()

                if not product_with_barcode:
                    self.stdout.write(self.style.WARNING(f"Brand {target_brand.name} has no products with barcodes. Skipping."))
                    continue

                # 5. Run scraper
                success = scraper.run(
                    barcode=product_with_barcode.barcode,
                    target_brand=target_brand,
                    output_file=output_file
                )

                if success:
                    successful_scrapes += 1

                # 6. Wait
                if successful_scrapes < 30:
                    self.stdout.write("Waiting 5 seconds before next scrape...")
                    time.sleep(5)
            
            self.stdout.write(self.style.SUCCESS(f'--- GS1 Scraper Run Complete. {successful_scrapes} new records saved to inbox. ---'))
