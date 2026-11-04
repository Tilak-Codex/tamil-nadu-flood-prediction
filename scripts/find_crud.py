import urllib.request
import re

url = "https://ffs.india-water.gov.in/main-es2015.fbfe583eb00a8117cb6c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode("utf-8", errors="ignore")
    # find methods calling this.http
    matches = re.findall(r'this\.http\.[a-z]+\(`\$\{this\.serviceUrl\}[^`]+`', js)
    print("Methods calling this.serviceUrl:")
    for m in set(matches[:25]):
        print("  ", m)
