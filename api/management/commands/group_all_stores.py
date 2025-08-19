from django.core.management.base import BaseCommand
from companies.models import Company
from api.analysers.store_grouping import group_stores_by_price_correlation

class Command(BaseCommand):
    help = 'Groups stores by price correlation for all companies and saves the result to a file.'

    def handle(self, *args, **options):
        self.stdout.write("Starting store grouping analysis for all companies...")

        results = []
        companies = Company.objects.all()

        for company in companies:
            self.stdout.write(f"Analyzing {company.name}...")
            groups, island_stores = group_stores_by_price_correlation(company.name)
            results.append((company, groups, island_stores))

        output_string = self.format_results(results)
        output_file = 'store_grouping_results.txt'
        with open(output_file, 'w') as f:
            f.write(output_string)

        self.stdout.write(self.style.SUCCESS(f"Analysis complete. Results saved to {output_file}"))

    def format_results(self, results):
        output = ["Store Grouping Analysis Results", "===============================\n"]

        for company, groups, island_stores in results:
            output.append(f"Company: {company.name}")
            output.append("-" * (len(company.name) + 10))

            if groups:
                output.append("Groups:")
                for i, group in enumerate(groups, 1):
                    output.append(f"- Group {i}:")
                    for store in group:
                        output.append(f"  - {store.store_name}")
            else:
                output.append("No store groups found.")

            if island_stores:
                output.append("\nIsland Stores (not in any group):")
                for store in island_stores:
                    output.append(f"- {store.store_name}")
            else:
                output.append("No island stores found.")

            output.append("\n===============================\n")

        return "\n".join(output)
