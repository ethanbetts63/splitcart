from django.core.management.base import BaseCommand
from django.db.models import Count, Q, F
from products.models import Product, ProductSubstitution

class Command(BaseCommand):
    help = 'Analyzes the quality and distribution of generated product substitutions.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample',
            type=int,
            default=0,
            help='Display a random sample of N substitutions for manual review.'
        )
        parser.add_argument(
            '--type',
            type=str,
            help='Filter samples by a specific type (e.g., SIZE, VARIANT).'
        )
        parser.add_argument(
            '--hubs',
            type=int,
            default=0,
            help='Show the top N products with the most substitution links.'
        )

    def handle(self, *args, **options):
        sample_size = options['sample']
        sub_type = options['type']
        hub_count = options['hubs']

        self._show_overall_stats()

        if hub_count > 0:
            self._show_hub_products(hub_count)

        if sample_size > 0:
            self._show_random_samples(sample_size, sub_type)

    def _show_overall_stats(self):
        self.stdout.write(self.style.SUCCESS("\n--- Overall Substitution Statistics ---"))
        
        total_products = Product.objects.count()
        total_substitutions = ProductSubstitution.objects.count()

        if total_substitutions == 0:
            self.stdout.write("No substitutions found in the database.")
            return

        # Find the number of unique products that have at least one substitution
        products_in_subs_a = ProductSubstitution.objects.values_list('product_a_id', flat=True)
        products_in_subs_b = ProductSubstitution.objects.values_list('product_b_id', flat=True)
        products_with_subs_count = len(set(list(products_in_subs_a) + list(products_in_subs_b)))

        self.stdout.write(f"- Total Products in DB: {total_products}")
        self.stdout.write(f"- Total Substitution Links: {total_substitutions}")
        self.stdout.write(f"- Products with at least one substitute: {products_with_subs_count} ({products_with_subs_count/total_products:.2%})")

        self.stdout.write("\n--- Substitutions by Type ---")
        type_counts = ProductSubstitution.objects.values('type').annotate(count=Count('type')).order_by('-count')
        for item in type_counts:
            percentage = (item['count'] / total_substitutions) * 100
            self.stdout.write(f"- {item['type']}: {item['count']} ({percentage:.2f}%)")

    def _show_hub_products(self, hub_count):
        self.stdout.write(self.style.SUCCESS(f"\n--- Top {hub_count} Substitution Hubs ---"))
        
        # Annotate products with the count of their substitution links
        # This is a simplified approach; a more complex query could be more precise
        # but this is a good indicator.
        hub_products = Product.objects.annotate(
            num_subs=Count('substitutions_a', distinct=True) + Count('substitutions_b', distinct=True)
        ).order_by('-num_subs')[:hub_count]

        for i, product in enumerate(hub_products):
            self.stdout.write(f"  {i+1}. \"{product.name}\" ({product.brand}) - {product.num_subs} links")

    def _show_random_samples(self, sample_size, sub_type):
        self.stdout.write(self.style.SUCCESS(f"\n--- Random Sample of {sample_size} Substitutions ---"))
        if sub_type:
            self.stdout.write(self.style.SUCCESS(f"--- (Filtered by Type: {sub_type.upper()}) ---"))

        queryset = ProductSubstitution.objects.all()
        if sub_type:
            queryset = queryset.filter(type__iexact=sub_type)

        if queryset.count() == 0:
            self.stdout.write(self.style.WARNING("No substitutions found matching the specified criteria."))
            return

        # Get random samples
        random_samples = queryset.order_by('?')[:sample_size]

        for i, sub in enumerate(random_samples):
            self.stdout.write(f"\n--- Sample {i+1}/{sample_size} (Type: {sub.type}, Score: {sub.score}) ---")
            self.stdout.write(f"  [A] {sub.product_a.name} ({sub.product_a.brand})")
            self.stdout.write(f"  [B] {sub.product_b.name} ({sub.product_b.brand})")
