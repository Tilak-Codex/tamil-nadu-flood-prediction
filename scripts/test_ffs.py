import urllib.request
import re
import json

def check_ffs():
    try:
        req = urllib.request.Request("https://ffs.india-water.gov.in/", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # find script tags
            scripts = re.findall(r'<script[^>]+src=[\'"]([^\'"]+)[\'"]', html)
            print("FFS scripts:", scripts)
            # find any endpoints in js
            base = "https://ffs.india-water.gov.in/"
            for s in scripts:
                if "main" in s or "app" in s or "runtime" in s:
                    full_url = s if s.startswith("http") else base + s.lstrip("/")
                    try:
                        req_js = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req_js, timeout=10) as js_resp:
                            js_text = js_resp.read().decode("utf-8", errors="ignore")
                            apis = re.findall(r'["\'](https?://[^"\']+|/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+)["\']', js_text)
                            matching = [a for a in apis if any(k in a.lower() for k in ["station", "hydro", "water", "flood", "level", "basin"])]
                            print(f"Candidate APIs in {s}:", set(matching[:10]))
                    except Exception as err:
                        print(f"Error fetching {full_url}:", err)
    except Exception as e:
        print("FFS error:", e)

if __name__ == "__main__":
    check_ffs()
