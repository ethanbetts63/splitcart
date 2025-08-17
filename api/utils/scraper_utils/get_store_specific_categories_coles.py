
import requests

def get_store_specific_categories(session):
    """
    Fetches and parses store-specific categories from the Coles GraphQL API.
    """
    api_url = "https://www.coles.com.au/api/graphql"
    
    # This GraphQL query is based on the structure of the API response.
    graphql_query = {
        "operationName": "menuItems",
        "variables": {},
        "query": """
            query menuItems {
                menuItems {
                    items {
                        ...menuItemFields
                        childItems {
                            ...menuItemFields
                            childItems {
                                ...menuItemFields
                            }
                        }
                    }
                }
            }
            fragment menuItemFields on MenuItem {
                id
                name
                seoToken
                productCount
            }
        """
    }

    try:
        response = session.post(api_url, json=graphql_query, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        all_slugs = set()
        items = data.get("data", {}).get("menuItems", {}).get("items", [])
        
        def extract_slugs(items_list):
            for item in items_list:
                if item.get("seoToken") and item.get("productCount", 0) > 0:
                    all_slugs.add(item["seoToken"])
                if "childItems" in item and item["childItems"]:
                    extract_slugs(item["childItems"])
        
        extract_slugs(items)
        return list(all_slugs)

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Could not fetch categories from Coles API: {e}")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while parsing categories: {e}")
        return []
