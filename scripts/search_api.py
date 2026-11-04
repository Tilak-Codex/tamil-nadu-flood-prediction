import urllib.request
import re

url = "https://ffs.india-water.gov.in/main-es2015.fbfe583eb00a8117cb6c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode("utf-8", errors="ignore")
    # find occurrences of '/api/'
    matches = re.findall(r'.{0,50}/api/[a-zA-Z0-9_\-]+.{0,50}', js)
    for m in matches[:15]:
        print("API MATCH:", m)
