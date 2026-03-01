import requests
import json

def _find_leaf_categories(nodes: list) -> list:
    """
    A recursive helper function to traverse the category tree and find all 
    nodes that have no children (the "leaf" nodes).
    
    Args:
        nodes: A list of category nodes from the hierarchy.

    Returns:
        A flat list of tuples, where each tuple contains the 
        'urlSlugText' and 'key' of each leaf category.
    """
    leaf_categories = []
    for node in nodes:
        children = node.get('children', [])
        if not children:
            # This is a leaf node, add its urlSlugText and key to our list
            if 'urlSlugText' in node and 'key' in node:
                leaf_categories.append(
                    (node['urlSlugText'], node['key'])
                )
        else:
            # This is not a leaf node, so we go deeper
            leaf_categories.extend(_find_leaf_categories(children))
    return leaf_categories

def get_aldi_categories(command, store_id: str, session: requests.Session) -> list:
    """
    Fetches the category hierarchy for a specific ALDI store and extracts a list
    of all the leaf subcategories to be scraped.

    Args:
        command: The command object for writing output.
        store_id: The unique identifier for the ALDI store (e.g., 'G452').
        session: The requests.Session object to use for the api call.

    Returns:
        A list of (urlSlugText, key) tuples to scrape, or an empty list if an error occurs.
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
