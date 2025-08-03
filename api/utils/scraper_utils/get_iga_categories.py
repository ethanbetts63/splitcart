import requests
import json

def _find_leaf_categories(nodes: list) -> list:
    """
    A recursive helper function to traverse the category tree and find all 
    nodes that have no children (the "leaf" nodes).
    
    Args:
        nodes: A list of category nodes from the hierarchy.

    Returns:
        A flat list of the 'displayName' of each leaf category.
    """
    leaf_categories = []
    for node in nodes:
        children = node.get('children', [])
        if not children:
            # This is a leaf node, add its name to our list
            if 'displayName' in node:
                leaf_categories.append(node['displayName'])
        else:
            # This is not a leaf node, so we go deeper
            leaf_categories.extend(_find_leaf_categories(children))
    return leaf_categories

def get_iga_categories(store_id: str, session: requests.Session) -> list:
    """
    Fetches the category hierarchy for a specific IGA store and extracts a list
    of all the leaf subcategories to be scraped.

    Args:
        store_id: The unique identifier for the IGA store.
        session: The requests.Session object to use for the API call.

    Returns:
        A list of specific subcategory names to scrape, or an empty list if an error occurs.
    """
    print(f"    Fetching category hierarchy for store ID: {store_id}...")
    api_url = f"https://www.igashop.com.au/api/storefront/stores/{store_id}/categoryHierarchy"
    
    try:
        response = session.get(api_url, timeout=60)
        response.raise_for_status()
        hierarchy_data = response.json()
        
        # The actual categories are nested under 'children' of the root object
        root_nodes = hierarchy_data.get('children', [])
        
        leaf_categories = _find_leaf_categories(root_nodes)
        
        print(f"    Successfully extracted {len(leaf_categories)} specific subcategories.")
        return leaf_categories

    except requests.exceptions.RequestException as e:
        print(f"    ERROR: Could not fetch category hierarchy for store {store_id}. Error: {e}")
    except json.JSONDecodeError:
        print(f"    ERROR: Failed to decode JSON for category hierarchy for store {store_id}.")
    
    return []
