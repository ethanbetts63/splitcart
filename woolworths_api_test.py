
import requests
import time

WOOLWORTHS_API_URL = "https://www.woolworths.com.au/api/v3/ui/fulfilment/stores"

headers = {
    "user-agent": "SplitCartScraper/1.0 (Contact: admin@splitcart.com)",
    "referer": "https://www.woolworths.com.au/",
    "accept": "application/json, text/plain, */*",
}

with open("woolworths_api_test_results.txt", "w") as f:
    for i in range(30):
        postcode = 6000 + i
        params = {"postcode": str(postcode)}
        
        start_time = time.time()
        try:
            response = requests.get(WOOLWORTHS_API_URL, headers=headers, params=params, timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            result = f"Postcode: {postcode}, Status Code: {response.status_code}, Response Time: {response_time:.2f} seconds\n"
            print(result)
            f.write(result)
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time
            error_result = f"Postcode: {postcode}, Error: {e}, Time elapsed: {response_time:.2f} seconds\n"
            print(error_result)
            f.write(error_result)

        time.sleep(0.5) # To be a good internet citizen :)
