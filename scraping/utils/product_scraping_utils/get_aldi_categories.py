import requests
import json

_ALDI_PROMOTIONAL_ROOTS = frozenset({
    'christmas',
    'limited time only',
    'front of store',
    'seasonal',
    'weekly specials',
    'special buys',
})


def _find_leaf_categories(nodes: list, path: list = None) -> list:
    path = path or []
    leaf_categories = []
    for node in nodes:
        name = node.get('name') or ''
        # Skip promotional subtrees at the root level
        if not path and name.lower() in _ALDI_PROMOTIONAL_ROOTS:
            continue
        children = node.get('children', [])
        current_path = path + [name]
        if not children:
            if 'urlSlugText' in node and 'key' in node:
                leaf_categories.append((node['urlSlugText'], node['key']))
        else:
            leaf_categories.extend(_find_leaf_categories(children, current_path))
    return leaf_categories


def get_aldi_categories(command, store_id: str, session: requests.Session) -> list:
    """
    Fetches the category hierarchy for a specific ALDI store and extracts a list
    of all the leaf subcategories to be scraped. Skips known promotional root categories.
    """
    command.stdout.write(f"    Fetching category hierarchy for store ID: {store_id}...")

    api_url = f"https://api.aldi.com.au/v2/product-category-tree?serviceType=walk-in&servicePoint={store_id}"

    try:
        response = session.get(api_url, timeout=60)
        response.raise_for_status()
        hierarchy_data = response.json()

        root_nodes = hierarchy_data.get('data', [])

        leaf_categories = _find_leaf_categories(root_nodes)

        command.stdout.write(f"    Successfully extracted {len(leaf_categories)} specific subcategories.")
        return leaf_categories

    except requests.exceptions.RequestException as e:
        command.stdout.write(f"    ERROR: Could not fetch category hierarchy for store {store_id}. Error: {e}\n")
        raise
    except json.JSONDecodeError:
        command.stdout.write(f"    ERROR: Failed to decode JSON for category hierarchy for store {store_id}.\n")

    return []
