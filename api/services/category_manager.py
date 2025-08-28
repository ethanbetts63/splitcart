from products.models import Product
from companies.models import Category

class CategoryManager:
    """
    Handles the creation of categories and their relationships to products.
    """
    def __init__(self, command):
        self.command = command
        self.category_cache = {c.name: c for c in Category.objects.all()}

    def process_categories(self, consolidated_data, product_cache):
        """
        The main method to orchestrate category processing.
        """
        self.command.stdout.write("--- Pass 3: Batch creating category relationships ---")
        
        all_category_paths = self._collect_all_paths(consolidated_data)
        self._create_new_categories(all_category_paths)
        self._create_parent_child_links(all_category_paths)
        self._link_products_to_categories(consolidated_data, product_cache)

    def _collect_all_paths(self, consolidated_data):
        """Collects all unique category paths from the data."""
        all_paths = set()
        for data in consolidated_data.values():
            # Assuming category_path is stored in product_details
            path = data.get('product_details', {}).get('category_path')
            if path and isinstance(path, list):
                all_paths.add(tuple(path))
        return all_paths

    def _create_new_categories(self, all_category_paths):
        """Part A: Ensuring all categories exist."""
        self.command.stdout.write("  Part A: Ensuring all categories exist...")
        existing_names = set(self.category_cache.keys())
        all_names = {name for path in all_category_paths for name in path}
        new_names = all_names - existing_names

        if not new_names:
            self.command.stdout.write("    - No new categories to create.")
            return

        self.command.stdout.write(f"    - Creating {len(new_names)} new categories...")
        new_categories = [Category(name=name) for name in new_names]
        Category.objects.bulk_create(new_categories)
        
        # Refresh cache
        for category in new_categories:
            self.category_cache[category.name] = category

    def _create_parent_child_links(self, all_category_paths):
        """Part B: Creating parent-child relationships."""
        self.command.stdout.write("  Part B: Creating parent-child relationships...")
        CategoryParents = Category.parents.through
        links_to_create = []
        
        # To avoid creating duplicate links in the bulk create list
        seen_links = set()

        for path in all_category_paths:
            for i in range(len(path) - 1):
                parent_name = path[i]
                child_name = path[i+1]
                parent_cat = self.category_cache.get(parent_name)
                child_cat = self.category_cache.get(child_name)

                if parent_cat and child_cat:
                    link_key = (parent_cat.id, child_cat.id)
                    if link_key not in seen_links:
                        links_to_create.append(
                            CategoryParents(from_category_id=parent_cat.id, to_category_id=child_cat.id)
                        )
                        seen_links.add(link_key)
        
        if links_to_create:
            self.command.stdout.write(f"    - Creating {len(links_to_create)} unique parent-child links...")
            CategoryParents.objects.bulk_create(links_to_create, ignore_conflicts=True, batch_size=999)

    def _link_products_to_categories(self, consolidated_data, product_cache):
        """Part C: Creating product-category relationships."""
        self.command.stdout.write("  Part C: Creating product-category relationships...")
        ProductCategory = Product.category.through
        links_to_create = []

        for key, data in consolidated_data.items():
            product = product_cache.get(key)
            path = data.get('product_details', {}).get('category_path')
            if product and path:
                # Link product to the most specific (last) category in the path
                leaf_category_name = path[-1]
                category = self.category_cache.get(leaf_category_name)
                if category:
                    links_to_create.append(
                        ProductCategory(product_id=product.id, category_id=category.id)
                    )
        
        if links_to_create:
            self.command.stdout.write(f"    - Creating {len(links_to_create)} product-category links...")
            ProductCategory.objects.bulk_create(links_to_create, ignore_conflicts=True, batch_size=999)
