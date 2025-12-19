import json, os
from pathlib import Path
import requests

url = "http://0.0.0.0:8324/insert"

headers = {
    "User-Agent": "PostmanRuntime/7.49.1",
    "Authorization": "Bearer ashpazyar-chroma-token-1234",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br"
}

input_path = open("Ashpazyar-data.jsonl", "r")

items = []
counter = 0

for line in input_path.readlines():
    
    record = json.loads(line)
    items.append(record)

    if counter % 2 == 1:

        body = { "recipes" : items }
        
        try:
            # Use requests.get() and pass the headers dictionary
            response = requests.post(url, headers=headers, json=body, timeout=10)
            
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status() 

            response.encoding = 'utf-8'
            
            print(f"✅ Request successful! Status Code: {response.status_code}")
            items = []
            # The .text attribute contains the response body (HTML content)

            
        except requests.exceptions.HTTPError as e:
            print(f"❌ ERROR: HTTP Error occurred (Status Code: {response.status_code}): {e}")
            print(body)
            break

        except requests.exceptions.ConnectionError as e:
            print(f"❌ ERROR: Connection Error occurred (Could not resolve DNS or connect): {e}")

        except requests.exceptions.Timeout as e:
            print(f"❌ ERROR: Timeout occurred (Request took too long): {e}")

        except requests.exceptions.RequestException as e:
            # Catches all other requests exceptions
            print(f"❌ ERROR: An unexpected request error occurred: {e}")

        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
    

    counter += 1
