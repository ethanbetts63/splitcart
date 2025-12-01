from django.core.management.base import BaseCommand
from django.db.models import Avg, Max, Min, Count
from products.models import ProductPriceSummary

class Command(BaseCommand):
    help = 'Provides an overview of the existing ProductPriceSummary data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Generating Product Price Summaries Overview..."))

        summary_count = ProductPriceSummary.objects.count()

        if summary_count == 0:
            self.stdout.write(self.style.WARNING("No product price summaries found in the database."))
            return

        self.stdout.write(f"Total Summaries: {summary_count}")

        # Aggregate discount stats
        discount_stats = ProductPriceSummary.objects.aggregate(
            avg_discount=Avg('best_possible_discount'),
            max_discount=Max('best_possible_discount'),
            min_discount=Min('best_possible_discount')
        )

        self.stdout.write("\n--- Discount Statistics ---")
        self.stdout.write(f"Average Discount: {discount_stats['avg_discount']:.2f}%")
        self.stdout.write(f"Maximum Discount: {discount_stats['max_discount']}%")
        self.stdout.write(f"Minimum Discount: {discount_stats['min_discount']}%")

        # Top 5 products with highest discount
        top_5_bargains = ProductPriceSummary.objects.order_by('-best_possible_discount').select_related('product')[:5]

        self.stdout.write("\n--- Top 5 Products by Max Possible Discount ---")
        for summary in top_5_bargains:
            self.stdout.write(
                f"- {summary.product.name} ({summary.product.brand.name if summary.product.brand else 'N/A'})"
                f" | {summary.best_possible_discount}% off"
                f" (Range: ${summary.min_price} - ${summary.max_price})"
            )
        
        # Breakdown by company count
        self.stdout.write("\n--- Breakdown by Company Count ---")
        company_breakdown = ProductPriceSummary.objects.values('company_count').annotate(count=Count('product_id')).order_by('-company_count')
        for item in company_breakdown:
            self.stdout.write(f"Products stocked by {item['company_count']} companies: {item['count']}")

        self.stdout.write(self.style.SUCCESS("\nOverview complete."))
