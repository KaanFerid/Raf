import requests
import re

url = "https://drive.google.com/uc?export=download&id=1EtuLCkRDRF1n9WBXVSfKLyP2o04OOtIH"

session = requests.Session()
res = session.get(url, stream=True)

print("Initial Content-Type:", res.headers.get("Content-Type"))

# If it's HTML, we need to bypass warning
if "text/html" in res.headers.get("Content-Type", ""):
    print("Warning page detected, attempting bypass...")
    
    # We read the HTML text to parse inputs
    html = res.text
    
    # Extract hidden inputs
    confirm_match = re.search(r'name="confirm"\s+value="([^"]+)"', html)
    uuid_match = re.search(r'name="uuid"\s+value="([^"]+)"', html)
    
    if confirm_match and uuid_match:
        confirm_val = confirm_match.group(1)
        uuid_val = uuid_match.group(1)
        print(f"Extracted confirm: {confirm_val}, uuid: {uuid_val}")
        
        # Second request with parameters
        download_url = "https://drive.usercontent.google.com/download"
        params = {
            "id": "1EtuLCkRDRF1n9WBXVSfKLyP2o04OOtIH",
            "export": "download",
            "confirm": confirm_val,
            "uuid": uuid_val
        }
        res2 = session.get(download_url, params=params, stream=True)
        print("Final Status Code:", res2.status_code)
        print("Final Content-Type:", res2.headers.get("Content-Type"))
        print("Final Content-Length:", res2.headers.get("Content-Length"))
        
        # Read first 100 bytes to check signature
        first_bytes = res2.raw.read(100)
        print("First bytes:", first_bytes[:20])
    else:
        print("Failed to extract confirmation parameters!")
else:
    print("Direct download worked directly without bypass.")
