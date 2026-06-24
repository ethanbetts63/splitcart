import requests

EXCLUDED_ROOT_SLUGS = {
    'specials',
    'everyday-market',
    'big-night-in',
    'dinner',
    'lunch-box',
    'front-of-store',
}


def _node_name(node):
    return node.get('Description') or node.get('DisplayName') or node.get('Name')


def _is_special_node(node):
    slug = node.get('UrlFriendlyName') or ''
    node_id = node.get('NodeId') or ''
    return slug.endswith('-specials') or node_id.endswith('_SPECIALS')


def _find_leaf_categories(nodes, path=None):
    path = path or []
    leaf_categories = []

    for node in nodes:
        if _is_special_node(node):
            continue

        name = _node_name(node)
        slug = node.get('UrlFriendlyName')
        node_id = node.get('NodeId')
        if not name or not slug or not node_id:
            continue

        category_path = path + [name]
        children = node.get('Children', [])

        if children:
            leaf_categories.extend(_find_leaf_categories(children, category_path))
        else:
            leaf_categories.append({
                'slug': slug,
                'node_id': node_id,
                'category_path': category_path,
            })

    return leaf_categories


def get_woolworths_categories(command):
    """
    Fetches the category hierarchy from Woolworths' api and extracts leaf categories
    with their canonical category paths.
    """
    api_url = "https://www.woolworths.com.au/apis/ui/PiesCategoriesWithSpecials"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'origin': 'https://www.woolworths.com.au',
        'referer': 'https://www.woolworths.com.au/',
        'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        command.stdout.write(f"ERROR: Request failed when fetching categories: {e}\n")
        raise
    except ValueError: # Catches JSON decoding errors
        command.stdout.write("ERROR: Failed to decode JSON when fetching categories.\n")
        return []

    roots = [
        category for category in data.get('Categories', [])
        if category.get('UrlFriendlyName') not in EXCLUDED_ROOT_SLUGS
    ]
    return _find_leaf_categories(roots)
