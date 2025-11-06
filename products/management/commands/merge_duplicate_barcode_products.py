from django.core.management.base import BaseCommand
from products.models import Product, Price, PriceRecord
from django.db.models import Count
from data_management.utils.price_normalizer import PriceNormalizer

class Command(BaseCommand):
    help = 'Finds and merges products with duplicate barcodes.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Finding duplicate barcodes...'))
        
        duplicate_barcodes = (
            Product.objects.values('barcode')
            .annotate(barcode_count=Count('barcode'))
            .filter(barcode_count__gt=1)
            .exclude(barcode__isnull=True)
            .exclude(barcode='')
        )

        if not duplicate_barcodes:
            self.stdout.write(self.style.SUCCESS('No duplicate barcodes found.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {len(duplicate_barcodes)} duplicate barcode(s).'))

        for item in duplicate_barcodes:
            barcode = item['barcode']
            self.stdout.write(self.style.WARNING(f'  - Processing duplicate barcode: {barcode}'))
            
            products_with_barcode = Product.objects.filter(barcode=barcode).order_by('id')
            
            canonical_product = products_with_barcode.first()
            self.stdout.write(self.style.SUCCESS(f'    - Canonical product: {canonical_product.name} (PK: {canonical_product.id})'))
            
            duplicate_products = products_with_barcode.exclude(id=canonical_product.id)
            for duplicate_product in duplicate_products:
                self._merge_products(canonical_product, duplicate_product)

        self.stdout.write(self.style.SUCCESS('Successfully merged duplicate barcode products.'))

    def _merge_products(self, canonical, duplicate):
        self.stdout.write(f"    - Merging '{duplicate.name}' (PK: {duplicate.id}) into canonical product.")
        
        update_fields = {}
        fields_to_check = ['url', 'aldi_image_url']
        for field_name in fields_to_check:
            if not getattr(canonical, field_name) and getattr(duplicate, field_name):
                update_fields[field_name] = getattr(duplicate, field_name)


        if duplicate.name_variations:
            merged_variations = canonical.name_variations or []
            added_new_variation = False
            for variation in duplicate.name_variations:
                if variation not in merged_variations:
                    merged_variations.append(variation)
                    added_new_variation = True
            if added_new_variation:
                update_fields['name_variations'] = merged_variations
        
        if update_fields:
            Product.objects.filter(pk=canonical.pk).update(**update_fields)

        prices_to_move = Price.objects.filter(price_record__product=duplicate).select_related('price_record')
        canonical_price_keys = set(
            (p.store_id, p.scraped_date) for p in Price.objects.filter(price_record__product=canonical)
        )

        for price in prices_to_move:
            price_key = (price.store_id, price.scraped_date)
            if price_key not in canonical_price_keys:
                old_price_record = price.price_record
                new_price_record, created = PriceRecord.objects.get_or_create(
                    product=canonical,
                    price=old_price_record.price,
                    was_price=old_price_record.was_price,
                    unit_price=old_price_record.unit_price,
                    unit_of_measure=old_price_record.unit_of_measure,
                    per_unit_price_string=old_price_record.per_unit_price_string,
                    is_on_special=old_price_record.is_on_special
                )
                price.price_record = new_price_record
                price_data = {
                    'product_id': canonical.id,
                    'store_id': price.store_id,
                    'price': new_price_record.price,
                    'date': price.scraped_date
                }
                normalizer = PriceNormalizer(price_data=price_data, company=price.store.company.name)
                price.normalized_key = normalizer.get_normalized_key()
                price.save()
            else:
                price.delete()

        duplicate.delete()