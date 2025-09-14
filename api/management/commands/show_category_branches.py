from django.core.management.base import BaseCommand
from companies.models import Company, Category
import random

class Command(BaseCommand):
    help = 'Shows a few sample, full branches from the category tree to verify its integrity.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            required=True,
            help='The name of the company to show branches for.'
        )
        parser.add_argument(
            '--num-branches',
            type=int,
            default=5,
            help='The number of sample branches to show.'
        )

    def _get_all_descendants(self, category, visited=None):
        """Recursively finds all descendants for a given category."""
        if visited is None:
            visited = set()
        
        if category.id in visited:
            return []
        
        visited.add(category.id)
        descendants = [category]
        # Use prefetch_related for efficiency if this becomes slow
        for child in category.subcategories.all():
            descendants.extend(self._get_all_descendants(child, visited))
            
        return descendants

    def handle(self, *args, **options):
        company_name = options['company_name']
        num_branches = options['num_branches']

        self.stdout.write(self.style.SUCCESS(f"--- Showing {num_branches} sample branches for {company_name} ---"))

        try:
            company = Company.objects.get(name__iexact=company_name)
        except Company.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Company '{company_name}' not found."))
            return

        root_categories = list(Category.objects.filter(company=company, parents__isnull=True).order_by('name'))

        if not root_categories:
            self.stderr.write(self.style.ERROR(f"No root categories found for {company_name}."))
            return

        sample_roots = random.sample(root_categories, min(len(root_categories), num_branches))

        for root in sample_roots:
            self.stdout.write(f"\n--- Branch from root: '{self.style.SQL_FIELD(root.name)}' ---")

            descendants = self._get_all_descendants(root)
            leaf_nodes = [desc for desc in descendants if desc.subcategories.count() == 0]

            if not leaf_nodes:
                self.stdout.write(f"  {root.name} (This root has no leaf nodes)")
                continue

            sample_leaf = random.choice(leaf_nodes)

            path = [sample_leaf]
            curr = sample_leaf
            # Trace back to the root, max 20 levels to prevent infinite loops in case of unexpected data
            for _ in range(20):
                if curr.id == root.id:
                    break
                parent = curr.parents.first()
                if not parent or parent in path:
                    break
                path.append(parent)
                curr = parent
            
            path.reverse()
            path_str = " -> ".join([c.name for c in path])
            self.stdout.write(f"  {path_str}")

        self.stdout.write(self.style.SUCCESS("\nBranch analysis complete."))