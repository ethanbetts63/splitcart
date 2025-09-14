from collections import defaultdict
from django.core.management.base import BaseCommand
from django.db.models import Q
from companies.models import Category, CategoryEquivalence

class Command(BaseCommand):
    help = 'Runs a verbose, step-by-step diagnostic of the Level 1 category matching logic.'

    def _calculate_levels(self):
        self.stdout.write("--- Step 1: Calculating category levels ---")
        levels = {}
        current_level = 0
        # Start with root categories (no parents)
        level_cats = list(Category.objects.filter(parents__isnull=True))
        processed_cats = set()

        while level_cats:
            next_level_cats = set()
            for cat in level_cats:
                if cat.id not in processed_cats:
                    levels[cat.id] = current_level
                    processed_cats.add(cat.id)
                    # Find all children for the next level
                    for sub_cat in cat.subcategories.all():
                        next_level_cats.add(sub_cat)
            level_cats = list(next_level_cats)
            current_level += 1
        
        # Print summary
        level_counts = defaultdict(int)
        for cat_id, level in levels.items():
            level_counts[level] += 1
        for level, count in sorted(level_counts.items()):
            self.stdout.write(f"  - Found {count} categories at Level {level}")
        
        return levels

    def handle(self, *args, **options):
        category_levels = self._calculate_levels()
        
        level_to_process = 1
        categories_at_level_ids = [cat_id for cat_id, lvl in category_levels.items() if lvl == level_to_process]
        all_cats_at_level_1 = list(Category.objects.filter(id__in=categories_at_level_ids).prefetch_related('parents', 'company'))

        if not all_cats_at_level_1:
            self.stdout.write(self.style.WARNING("\nNo categories found at Level 1. Cannot proceed."))
            return

        self.stdout.write(f"\n--- Step 2: Processing {len(all_cats_at_level_1)} categories found at Level 1 ---")

        parent_level = level_to_process - 1

        for cat1 in all_cats_at_level_1:
            self.stdout.write("="*50)
            self.stdout.write(f"Processing '{self.style.SQL_FIELD(cat1.name)}' ({cat1.company.name})...")

            # --- Find Parents ---
            parents = list(cat1.parents.all())
            if not parents:
                self.stdout.write("  - Parents: [] (This category has no parents, which may be an issue)")
                continue
            self.stdout.write(f"  - Found Parents: {[p.name for p in parents]}")

            # --- Find Equivalent Parents ---
            parent_equivalents = set()
            for parent in parents:
                if category_levels.get(parent.id) == parent_level:
                    equiv_links = CategoryEquivalence.objects.filter(
                        Q(from_category=parent) | Q(to_category=parent)
                    ).select_related('from_category', 'to_category')
                    
                    for link in equiv_links:
                        if link.from_category_id == parent.id:
                            parent_equivalents.add(link.to_category)
                        else:
                            parent_equivalents.add(link.from_category)
            
            if not parent_equivalents:
                self.stdout.write("  - Equivalent Parents in other companies: [] (No links found for its parents)")
                continue
            self.stdout.write(f"  - Found Equivalent Parents: {[p.name for p in parent_equivalents]}")

            # --- Find Candidate Pool ---
            candidate_pool = set()
            for equiv_parent in parent_equivalents:
                # Get children of the equivalent parent that are at the correct level
                for cat2 in equiv_parent.subcategories.filter(id__in=categories_at_level_ids):
                    if cat1.company_id != cat2.company_id:
                        candidate_pool.add(cat2)

            if not candidate_pool:
                self.stdout.write("  - Candidate Pool for matching: [] (Equivalent parents have no children at this level)")
                continue
            self.stdout.write(f"  - Generated Candidate Pool: {[c.name for c in candidate_pool]}")

        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("Debug run complete."))
