import urllib.request
import json

base = "https://ffs.india-water.gov.in/eswis-gis"
urls = [
    f"{base}/api/layer-station-geo/all",
    f"{base}/api/layer-station/all",
    f"{base}/api/flood-forecast-static/all",
    f"{base}/api/layer-station-geo",
]

for url in urls:
    print(f"Trying {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            print(f"  -> SUCCESS {resp.getcode()}, length {len(data)}")
            print("  -> Snippet:", data[:250])
    except Exception as e:
        print(f"  -> Failed: {e}")
