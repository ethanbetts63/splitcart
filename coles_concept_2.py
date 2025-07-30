import requests
import json
import re
import time

def extract_build_id_from_page(category_slug):
    """
    Extract the real build ID from the page source
    """
    print(f"🔍 Extracting build ID from page source...")
    
    session = requests.Session()
    session.headers.update({
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'upgrade-insecure-requests': '1',
    })
    
    try:
        url = f"https://www.coles.com.au/browse/{category_slug}"
        response = session.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to get page: {response.status_code}")
            return None, None
            
        html_content = response.text
        print(f"✅ Got page content ({len(html_content)} chars)")
        
        # Extract build ID using the pattern you found
        build_id_pattern = r'"buildId":"([^"]+)"'
        match = re.search(build_id_pattern, html_content)
        
        if match:
            build_id = match.group(1)
            print(f"✅ Found build ID: {build_id}")
            return build_id, session
        else:
            print("❌ Could not find build ID in page")
            # Save for debugging
            with open("debug_no_buildid.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            return None, None
            
    except Exception as e:
        print(f"❌ Error extracting build ID: {e}")
        return None, None

def fetch_coles_products(session, build_id, category_slug, page_number=1):
    """
    Fetch products using the real build ID
    """
    api_url = f"https://www.coles.com.au/_next/data/{build_id}/en/browse/{category_slug}.json"
    if page_number > 1:
        api_url += f"?page={page_number}"
        
    print(f"🛒 Fetching products from: {api_url}")
    
    # Update headers for API call
    session.headers.update({
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'referer': f'https://www.coles.com.au/browse/{category_slug}',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    })
    
    try:
        response = session.get(api_url, timeout=30)
        response.raise_for_status()
        
        print(f"✅ API Success! Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        data = response.json()
        
        # Extract products from the response
        page_props = data.get('pageProps', {})
        search_results = page_props.get('searchResults', {})
        products = search_results.get('results', [])
        total_results = search_results.get('totalRecordCount', 0)
        
        print(f"📦 Found {len(products)} products on this page")
        print(f"📊 Total products in category: {total_results}")
        
        return {
            'products': products,
            'total_count': total_results,
            'current_page': page_number,
            'page_props': page_props
        }
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text[:500]}...")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        print(f"Response: {response.text[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def display_products(products_data):
    """
    Display product information in a nice format
    """
    if not products_data or not products_data['products']:
        print("❌ No products to display")
        return
        
    products = products_data['products']
    print(f"\n🛒 COLES PRODUCTS ({len(products)} items)")
    print("=" * 80)
    
    for i, product in enumerate(products[:10], 1):  # Show first 10
        name = product.get('name', 'N/A')
        brand = product.get('brand', 'N/A')
        
        # Price information
        pricing = product.get('pricing', {})
        price_now = pricing.get('now', 'N/A')
        price_was = pricing.get('was', None)
        
        # Product details
        package_size = product.get('packageSize', 'N/A')
        availability = product.get('availability', {})
        in_stock = availability.get('isAvailable', False)
        
        print(f"{i:2d}. {name}")
        print(f"    Brand: {brand}")
        print(f"    Price: ${price_now}" + (f" (was ${price_was})" if price_was else ""))
        print(f"    Size: {package_size}")
        print(f"    In Stock: {'✅' if in_stock else '❌'}")
        print()

def main():
    """
    Main scraping function
    """
    category = "fruit-vegetables"
    
    print("🍎 COLES SCRAPER - Starting...")
    print(f"Category: {category}")
    
    # Step 1: Get the current build ID
    build_id, session = extract_build_id_from_page(category)
    
    if not build_id:
        print("❌ Failed to get build ID. Trying with the one you found...")
        # Use the build ID you manually found as fallback
        build_id = "20250725.2-16b00f604a80917a4801999dd2fbeb5771f98122"
        session = requests.Session()
        session.headers.update({
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        print(f"🔄 Using manual build ID: {build_id}")
    
    # Step 2: Fetch products
    products_data = fetch_coles_products(session, build_id, category, page_number=1)
    
    if products_data:
        print("🎉 SUCCESS! Retrieved Coles product data")
        display_products(products_data)
        
        # Save raw data for further processing
        with open("coles_products.json", "w", encoding="utf-8") as f:
            json.dump(products_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved raw data to 'coles_products.json'")
        
        return products_data
    else:
        print("❌ Failed to retrieve product data")
        return None

if __name__ == "__main__":
    result = main()
    
    if result:
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Products on page: {len(result['products'])}")
        print(f"   - Total in category: {result['total_count']}")
        print(f"   - Current page: {result['current_page']}")
    else:
        print(f"\n❌ Scraping failed. Check the debug output above.")