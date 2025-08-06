import re
import json
import html

def parse_stores_from_html(html_content):
    stores = []
    # Regex to find the store data from the data-storedata attribute
    store_data_matches = re.findall(r'data-storedata="([^"]+)"', html_content)

    for store_data_str in store_data_matches:
        # Decode HTML entities like &quot;
        decoded_str = html.unescape(store_data_str)
        try:
            store_data = json.loads(decoded_str)
            stores.append(store_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Problematic string: {decoded_str}")

    return stores

def main():
    with open('C:\\Users\\ethan\\coding\\splitcart\\stores_page.txt', 'r', encoding='utf-8') as f:
        jsonp_content = f.read()

    # Strip the JSONP padding
    start_index = jsonp_content.find('(')
    end_index = jsonp_content.rfind(')')

    if start_index != -1 and end_index != -1:
        json_str = jsonp_content[start_index + 1:end_index]
        try:
            data = json.loads(json_str)
            html_content = data.get('content', '')
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from JSONP: {e}")
            html_content = ''
    else:
        html_content = jsonp_content

    stores_data = parse_stores_from_html(html_content)

    with open('C:\\Users\\ethan\\coding\\splitcart\\stores.json', 'w', encoding='utf-8') as f:
        json.dump(stores_data, f, indent=4)

if __name__ == "__main__":
    main()
