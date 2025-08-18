from products.models import Product
from companies.models import Category, Company

def batch_create_category_relationships(consolidated_data: dict, product_cache: dict):
    """
    Pass 4: Create categories and all relationships in batches.
    """
    print("--- Pass 4: Batch creating category relationships ---")
    company_cache = {c.name: c for c in Company.objects.all()}
    
    # Part A: Ensure all categories exist
    print("  Part A: Ensuring all categories exist...")
    existing_categories = {(c.name.lower() if c.name else '', c.company_id): c for c in Category.objects.all()}
    all_category_names = set()
    for data in consolidated_data.values():
        for path in data['category_paths']:
            for name in path:
                all_category_names.add(name)

    new_categories_to_create = []
    # This is simplified; assumes company context is available for each category name.
    # A more robust implementation might need to associate company with each path.
    for data in consolidated_data.values():
        company = company_cache.get(data['company_name'])
        if not company: continue
        for path in data['category_paths']:
            for name in path:
                if (name.lower(), company.id) not in existing_categories:
                    new_categories_to_create.append(Category(name=name, company=company))
                    existing_categories[(name.lower(), company.id)] = True # Avoid duplicates

    if new_categories_to_create:
        print(f"  Creating {len(new_categories_to_create)} new categories...")
        Category.objects.bulk_create(new_categories_to_create, ignore_conflicts=True)
    
    category_cache = {(c.name.lower() if c.name else '', c.company_id): c for c in Category.objects.all()}

    # Part B: Create parent-child relationships
    print("  Part B: Creating parent-child relationships...")
    parent_relations_to_create = []
    CategoryParents = Category.parents.through
    for data in consolidated_data.values():
        company = company_cache.get(data['company_name'])
        if not company: continue
        for path in data['category_paths']:
            parent_obj = None
            for name in path:
                cat_obj = category_cache.get((name.lower(), company.id))
                if parent_obj and cat_obj:
                    parent_relations_to_create.append(CategoryParents(from_category_id=cat_obj.id, to_category_id=parent_obj.id))
                parent_obj = cat_obj
    
    if parent_relations_to_create:
        print(f"  Creating {len(parent_relations_to_create)} parent-child links...")
        CategoryParents.objects.bulk_create(parent_relations_to_create, ignore_conflicts=True)

    # Part C: Create product-category relationships
    print("  Part C: Creating product-category relationships...")
    ProductCategory = Product.category.through
    product_relations_to_create = []
    for key, data in consolidated_data.items():
        product_obj = product_cache.get(key)
        company = company_cache.get(data['company_name'])
        if not product_obj or not company: continue
        for path in data['category_paths']:
            if path:
                leaf_category_name = path[-1]
                cat_obj = category_cache.get((leaf_category_name.lower(), company.id))
                if cat_obj:
                    product_relations_to_create.append(ProductCategory(product_id=product_obj.id, category_id=cat_obj.id))

    if product_relations_to_create:
        print(f"  Creating {len(product_relations_to_create)} product-category links...")
        ProductCategory.objects.bulk_create(product_relations_to_create, ignore_conflicts=True)

    print("Category relationships complete.")
