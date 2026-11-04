import urllib.request
import re

url = "https://ffs.india-water.gov.in/main-es2015.fbfe583eb00a8117cb6c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode("utf-8", errors="ignore")
    # find all this.http.get calls with string literals
    calls = re.findall(r'this\.http\.get\([\'"]([^\'"]+)[\'"]', js)
    print("Static this.http.get paths:")
    for c in sorted(set(calls)):
        print("  ", c)
