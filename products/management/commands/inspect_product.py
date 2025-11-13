from django.core.management.base import BaseCommand
from products.models import Product
import json

class Command(BaseCommand):
    help = 'Inspects a product in the database by its primary key and returns all its details, including raw SKUs.'

    def add_arguments(self, parser):
        parser.add_argument('product_pk', type=int, help='The primary key of the product to inspect.')

    def handle(self, *args, **options):
        product_pk = options['product_pk']

        self.stdout.write(f"--- Inspecting Product with PK: {product_pk} ---")

        try:
            product = Product.objects.get(pk=product_pk)

            self.stdout.write(self.style.SUCCESS(f"Product found (PK: {product.pk}):"))
            
            # Get all concrete fields from the model
            for field in product._meta.concrete_fields:
                value = getattr(product, field.name)
                if field.name in ['sizes', 'normalized_name_brand_size_variations', 'brand_name_company_pairs']:
                    self.stdout.write(f"  {field.name}: {json.dumps(value)}")
                else:
                    self.stdout.write(f"  {field.name}: {value}")

            # Also include ManyToMany fields if they exist
            for field in product._meta.many_to_many:
                related_objects = getattr(product, field.name).all()
                if related_objects.exists():
                    self.stdout.write(f"  {field.name}: {[str(obj) for obj in related_objects]}")
                else:
                    self.stdout.write(f"  {field.name}: (empty)")

            # Explicitly show related SKUs
            self.stdout.write(self.style.HTTP_INFO("\n--- Related SKUs ---"))
            related_skus = product.skus.all()
            if related_skus.exists():
                for sku_obj in related_skus:
                    self.stdout.write(f"  - Company: {sku_obj.company.name}, SKU: {sku_obj.sku}")
            else:
                self.stdout.write("  (No associated SKUs found)")

        except Product.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Product with PK {product_pk} not found."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))

        self.stdout.write(self.style.SUCCESS("--- Inspection Complete ---"))
