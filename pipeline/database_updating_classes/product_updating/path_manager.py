from django.utils.text import slugify
from products.models import Product
from pipeline.utils.path_classifier import classify_path

BATCH_SIZE = 500


def _make_path_key(company_name: str, path: list) -> str:
    return f"{company_name.lower()}|{'/'.join(slugify(p) for p in path)}"


class PathManager:
    """
    Replaces CategoryManager. Merges incoming category_path evidence from each
    product into Product.category_paths. Does not create Category nodes or
    parent-child links.

    Each entry in category_paths:
    {
        "company": str,
        "path": [str],
        "path_key": str,          # "company|slug/slug/slug"
        "root_name": str,
        "leaf_name": str,
        "path_type": str,         # filled by Phase 4 classifier
        "canonical_key": str,     # filled by Phase 4 classifier
        "primary_category_slug": str,  # filled by Phase 5 generator
        "evidence_count": int,
    }
    """

    def __init__(self, command, caches, cache_updater):
        self.command = command
        self.caches = caches
        self.cache_updater = cache_updater

    def process(self, raw_product_data: list, company_obj) -> None:
        self.command.stdout.write(f"  - PathManager: Processing category paths for {company_obj.name}...")

        # Build {product_id: path} for products that have a category_path
        product_id_to_path: dict[int, list] = {}
        for data in raw_product_data:
            product_dict = data.get('product', {})
            path = product_dict.get('category_path')
            if not path or not isinstance(path, list):
                continue
            product_id = self.caches['products_by_norm_string'].get(
                product_dict.get('normalized_name_brand_size')
            )
            if product_id:
                product_id_to_path[product_id] = path

        if not product_id_to_path:
            self.command.stdout.write("    - No category paths found in file.")
            return

        self.command.stdout.write(f"    - Found category paths for {len(product_id_to_path)} products.")

        # Fetch current category_paths for all affected products in one query
        product_ids = list(product_id_to_path.keys())
        self.command.stdout.write(f"    - Fetching {len(product_ids)} products for category path update...")
        products = {
            p.id: p
            for p in Product.objects.filter(id__in=product_ids).only('id', 'category_paths')
        }
        self.command.stdout.write(f"    - Fetched {len(products)} products.")

        company_name = company_obj.name
        to_update = []
        classification_cache = {}
        processed_count = 0

        for product_id, path in product_id_to_path.items():
            product = products.get(product_id)
            if not product:
                continue

            path_key = _make_path_key(company_name, path)
            existing_paths: list = product.category_paths or []

            # Find existing entry for this company+path
            matched = next((e for e in existing_paths if e.get('path_key') == path_key), None)
            if matched:
                matched['evidence_count'] = matched.get('evidence_count', 1) + 1
            else:
                classification = classification_cache.get(path_key)
                if classification is None:
                    classification = classify_path(company_name, path)
                    classification_cache[path_key] = classification
                existing_paths.append({
                    'company': company_name,
                    'path': path,
                    'path_key': path_key,
                    'root_name': path[0] if path else '',
                    'leaf_name': path[-1] if path else '',
                    'path_type': classification['path_type'],
                    'canonical_key': classification['canonical_key'],
                    'primary_category_slug': classification['primary_category_slug'],
                    'evidence_count': 1,
                })

            product.category_paths = existing_paths
            to_update.append(product)
            processed_count += 1

            if processed_count % 5000 == 0:
                self.command.stdout.write(f"    - Prepared category_paths for {processed_count} products...")

        if to_update:
            self.command.stdout.write(
                f"    - Writing category_paths for {len(to_update)} products in batches of {BATCH_SIZE}..."
            )
            Product.objects.bulk_update(to_update, ['category_paths'], batch_size=BATCH_SIZE)
            self.command.stdout.write(f"    - Updated category_paths for {len(to_update)} products.")
