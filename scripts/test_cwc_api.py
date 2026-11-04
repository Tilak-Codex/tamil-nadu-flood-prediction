import urllib.request
import json

base = "https://ffs.india-water.gov.in"
endpoints = [
    "/api/layer-station",
    "/api/station-water-level-above-warning",
    "/api/flood-forecast-static",
]

for ep in endpoints:
    url = base + ep
    print(f"Testing {url}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            print(f"  -> SUCCESS {resp.getcode()}, length: {len(data)}")
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    print(f"  -> Returned {len(parsed)} items. Sample: {parsed[0] if len(parsed)>0 else 'empty'}")
                elif isinstance(parsed, dict):
                    print(f"  -> Keys: {list(parsed.keys())}")
            except Exception as je:
                print(f"  -> JSON parse error: {je}, snippet: {data[:200]}")
    except Exception as e:
        print(f"  -> FAILED: {e}")
