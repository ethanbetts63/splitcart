import requests
import re
import json

def save_html_response(content):
    filename = "coles_response.html"
    print(f"DEBUG: Saving the server's HTML response to '{filename}'...")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"DEBUG: HTML response saved successfully.")

def get_build_id(session):
    print("[STEP 1] Attempting to fetch the build_id from Coles homepage...")
    url = "https://www.coles.com.au"
    
    try:
        print("[STEP 2] Sending GET request to the server...")
        response = session.get(url, timeout=30)
        print(f"[STEP 3] Received response with Status Code: {response.status_code}")
        
        response.raise_for_status()
        
        html_content = response.text
        save_html_response(html_content)

        print("[STEP 4] Searching for the '__NEXT_DATA__' script tag in the HTML...")
        script_tag_match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', 
            html_content
        )

        if not script_tag_match:
            print("ERROR: Could not find the '__NEXT_DATA__' script tag. The server may have blocked the request or sent a different page.")
            return None

        print("[STEP 5] Found the script tag. Parsing its JSON content...")
        next_data_json = script_tag_match.group(1)
        
        try:
            next_data = json.loads(next_data_json)
            print("[STEP 6] JSON content parsed successfully.")
        except json.JSONDecodeError:
            print("ERROR: Failed to parse the content of the script tag as JSON.")
            return None

        print("[STEP 7] Extracting 'buildId' from the JSON data...")
        build_id = next_data.get("buildId")

        if build_id:
            print(f"SUCCESS: Found build_id: {build_id}")
            return build_id
        else:
            print("ERROR: Found '__NEXT_DATA__' but the 'buildId' key was not inside.")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"CRITICAL: HTTP Error occurred: {e}")
        print("DEBUG: This often happens if the server actively blocks you with a 4xx status code (e.g., 403 Forbidden).")
        save_html_response(e.response.text)
        return None
    except requests.exceptions.RequestException as e:
        print(f"CRITICAL: A network request error occurred: {e}")
        return None

def main():
    print("--- Starting Coles Scraper Concept (Debug Mode) ---")

    session = requests.Session()
    
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'referer': 'https://www.google.com/',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }
    session.headers.update(headers)

    build_id = get_build_id(session)

    if build_id:
        print("\nProcess finished successfully.")
    else:
        print("\nHalting script because build_id could not be retrieved. Please check 'coles_response.html' to see what the server sent back.")

    print("\n--- Script Finished ---")

if __name__ == "__main__":
    main()

