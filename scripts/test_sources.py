import urllib.request
import re
import json

def test_imd():
    print("--- Testing IMD ---")
    url = "https://api.imd.gov.in/public/api_reference.html"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            print(f"Loaded {len(html)} bytes from IMD reference")
            # find all URLs or paths mentioned
            endpoints = set(re.findall(r'https?://[^\s"\'<>]+|/v\d+/[^\s"\'<>]+|/[a-zA-Z0-9_\-/]+', html))
            matched = [ep for ep in endpoints if any(w in ep.lower() for w in ["api", "weather", "district", "city", "forecast"])]
            print(f"Found {len(matched)} candidate paths:")
            for m in sorted(matched)[:15]:
                print("  ", m)
    except Exception as e:
        print("IMD error:", e)

def test_cwc_nwdp():
    print("--- Testing CWC / NWDP ---")
    # CWC / NWIC India-WRIS endpoints
    urls = [
        "https://nwdp.nwic.gov.in/",
        "https://indiawris.gov.in/wris/",
        "https://ffs.india-water.gov.in/",
    ]
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                print(f"  {u} -> HTTP {resp.getcode()}")
        except Exception as e:
            print(f"  {u} -> Failed: {e}")

def test_tn_dashboard():
    print("--- Testing TN Flood Monitor ---")
    url = "https://chennaifloodmonitor.tn.gov.in/HomePage/Dashboard"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # look for ajax calls or api endpoints in the html
            api_calls = set(re.findall(r'(/[^"\'\s]+\.php|/[^"\'\s]+\.ashx|/api/[^"\'\s]+|https?://[^"\'\s]+)', html))
            print(f"  Dashboard loaded ({len(html)} bytes). Candidate URLs:")
            for a in sorted(api_calls)[:10]:
                print("   ", a)
    except Exception as e:
        print("  TN error:", e)

if __name__ == "__main__":
    test_imd()
    test_cwc_nwdp()
    test_tn_dashboard()
