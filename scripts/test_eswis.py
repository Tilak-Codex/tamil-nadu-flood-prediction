import urllib.request
import json

base = "https://ffs.india-water.gov.in/eswis-gis"
endpoints = [
    "/api/counter/getCurrentDayVisitorCount",
    "/api/layer-station",
    "/api/new-entry-data",
    "/api/master-basin-localriver"
]

for ep in endpoints:
    url = base + ep
    print(f"Testing {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            print(f"  -> SUCCESS {resp.getcode()}, length: {len(data)}")
            print(f"  -> Sample: {data[:200]}")
    except Exception as e:
        print(f"  -> FAILED: {e}")
