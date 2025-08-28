from products.models import Product
from companies.models import Category, Company
from django.utils.text import slugify

def batch_create_category_relationships(consolidated_data: dict, product_cache: dict):
    """
    Pass 4: Create categories and all relationships in batches.
    """
    print("--- Pass 4: Batch creating category relationships ---")
    company_cache = {c.name.lower(): c for c in Company.objects.all()}
    
    # Part A: Ensure all categories exist
    print("  Part A: Ensuring all categories exist...")
    existing_categories = {(c.slug, c.company_id): c for c in Category.objects.all()}
    all_category_names = set()
    for data in consolidated_data.values():
        for path in data['category_paths']:
            for name in path:
                all_category_names.add(name)

    new_categories_to_create = []
    for data in consolidated_data.values():
        company_name = data.get('company_name')
        if not company_name:
            continue
        company = company_cache.get(company_name.lower())
        if not company: continue
        for path in data['category_paths']:
            for name in path:
                slug = slugify(name)
                if (slug, company.id) not in existing_categories:
                    new_categories_to_create.append(Category(name=name, slug=slug, company=company))
                    existing_categories[(slug, company.id)] = True # Avoid duplicates

    if new_categories_to_create:
        print(f"  Creating {len(new_categories_to_create)} new categories...")
        Category.objects.bulk_create(new_categories_to_create, ignore_conflicts=True)
    
    category_cache = {(c.slug, c.company_id): c for c in Category.objects.all()}

    # Part B: Create parent-child relationships (Optimized)
    print("  Part B: Creating parent-child relationships...")
    parent_links_to_create = set() # Use a set to store unique (child_id, parent_id) tuples

    for data in consolidated_data.values():
        company_name = data.get('company_name')
        if not company_name:
            continue
        company = company_cache.get(company_name.lower())
        if not company: continue
        for path in data['category_paths']:
            parent_obj = None
            for name in path:
                slug = slugify(name)
                cat_obj = category_cache.get((slug, company.id))
                if parent_obj and cat_obj:
                    parent_links_to_create.add((cat_obj.id, parent_obj.id))
                parent_obj = cat_obj
    
    if parent_links_to_create:
        CategoryParents = Category.parents.through
        relations_to_bulk_create = [CategoryParents(from_category_id=child_id, to_category_id=parent_id) for child_id, parent_id in parent_links_to_create]
        print(f"  Creating {len(relations_to_bulk_create)} unique parent-child links...")
        CategoryParents.objects.bulk_create(relations_to_bulk_create, ignore_conflicts=True)

    # Part C: Create product-category relationships
    print("  Part C: Creating product-category relationships...")
    ProductCategory = Product.category.through
    product_relations_to_create = []
    for key, data in consolidated_data.items():
        product_obj = product_cache.get(key)
        company_name = data.get('company_name')
        if not company_name:
            continue
        company = company_cache.get(company_name.lower())
        if not product_obj or not company: continue
        for path in data['category_paths']:
            if path:
                leaf_category_name = path[-1]
                slug = slugify(leaf_category_name)
                cat_obj = category_cache.get((slug, company.id))
                if cat_obj:
                    product_relations_to_create.append(ProductCategory(product_id=product_obj.id, category_id=cat_obj.id))

    if product_relations_to_create:
        print(f"  Creating {len(product_relations_to_create)} product-category links...")
        ProductCategory.objects.bulk_create(product_relations_to_create, ignore_conflicts=True)

    print("Category relationships complete.")
