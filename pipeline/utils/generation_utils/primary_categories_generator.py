from django.db import transaction
from companies.models import PrimaryCategory
from products.models import Product
from pipeline.data.category_mappings import CATEGORY_MAPPINGS, PRIMARY_CATEGORY_HIERARCHY


_CANONICAL_PATH_TYPES = frozenset({'canonical_taxonomy'})
_FALLBACK_PATH_TYPES = frozenset({'canonical_taxonomy', 'dietary'})


class PrimaryCategoriesGenerator:
    """
    Generates PrimaryCategory objects and populates Product.primary_category_slugs.

    Replaces the old graph-traversal approach. Now reads Product.category_paths,
    which are already classified by PathClassifier (path_type, primary_category_slug).

    Steps:
    1. Delete and recreate PrimaryCategory objects from CATEGORY_MAPPINGS names.
    2. Set up PRIMARY_CATEGORY_HIERARCHY links.
    3. Populate Product.primary_category_slugs from category_paths.
    """

    def __init__(self, command):
        self.command = command
        self.stdout = command.stdout
        self.style = command.style

    def run(self):
        self._delete_existing_primary_categories()
        self._create_primary_categories()
        self._assign_sub_categories()
        self._populate_product_primary_category_slugs()
        self.stdout.write(self.style.SUCCESS("Successfully generated primary categories."))

    def _delete_existing_primary_categories(self):
        self.stdout.write("Deleting existing primary category objects...")
        deleted_count, _ = PrimaryCategory.objects.all().delete()
        self.stdout.write(f"Deleted {deleted_count} existing primary category objects.")

    def _create_primary_categories(self):
        self.stdout.write("Creating primary category objects...")
        names = set()
        for store_mappings in CATEGORY_MAPPINGS.values():
            names.update(v for v in store_mappings.values() if v is not None)
        for parent, children in PRIMARY_CATEGORY_HIERARCHY.items():
            names.add(parent)
            names.update(children)

        for name in names:
            PrimaryCategory.objects.get_or_create(name=name)
        self.stdout.write(f"Created {len(names)} unique primary categories.")

    def _assign_sub_categories(self):
        self.stdout.write("Assigning sub-categories to primary categories...")
        for parent_name, child_names in PRIMARY_CATEGORY_HIERARCHY.items():
            try:
                parent_cat = PrimaryCategory.objects.get(name=parent_name)
            except PrimaryCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Parent '{parent_name}' not found. Skipping."))
                continue
            for child_name in child_names:
                try:
                    child_cat = PrimaryCategory.objects.get(name=child_name)
                    parent_cat.sub_categories.add(child_cat)
                except PrimaryCategory.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Child '{child_name}' not found. Skipping."))

    def _populate_product_primary_category_slugs(self):
        """
        For each product, derive primary_category_slugs from category_paths entries
        that have a path_type of canonical_taxonomy. Falls back to including dietary
        paths if no canonical paths yield a slug.
        """
        self.stdout.write("Populating Product.primary_category_slugs from category_paths...")

        # Build set of valid slugs from known PrimaryCategory names
        valid_slugs = set(PrimaryCategory.objects.values_list('slug', flat=True))

        products = list(
            Product.objects.exclude(category_paths=[]).only('id', 'category_paths', 'primary_category_slugs')
        )

        to_update = []
        for product in products:
            slugs = _derive_primary_slugs(product.category_paths, valid_slugs)
            if slugs != set(product.primary_category_slugs or []):
                product.primary_category_slugs = sorted(slugs)
                to_update.append(product)

        if to_update:
            with transaction.atomic():
                Product.objects.bulk_update(to_update, ['primary_category_slugs'])
        self.stdout.write(f"Updated primary_category_slugs for {len(to_update)} products.")


def _derive_primary_slugs(category_paths: list, valid_slugs: set) -> set:
    """
    Return the set of primary_category_slugs for a product from its category_paths.
    Uses canonical_taxonomy paths first; falls back to including dietary if empty.
    """
    slugs = _collect_slugs(category_paths, _CANONICAL_PATH_TYPES, valid_slugs)
    if not slugs:
        slugs = _collect_slugs(category_paths, _FALLBACK_PATH_TYPES, valid_slugs)
    if not slugs:
        # Last resort: any path with a primary_category_slug
        slugs = {
            e['primary_category_slug']
            for e in category_paths
            if e.get('primary_category_slug') and e['primary_category_slug'] in valid_slugs
        }
    return slugs


def _collect_slugs(category_paths: list, allowed_types: frozenset, valid_slugs: set) -> set:
    return {
        e['primary_category_slug']
        for e in category_paths
        if e.get('path_type') in allowed_types
        and e.get('primary_category_slug')
        and e['primary_category_slug'] in valid_slugs
    }
