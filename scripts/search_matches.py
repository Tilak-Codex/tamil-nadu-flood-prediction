import urllib.request
import re

url = "https://ffs.india-water.gov.in/main-es2015.fbfe583eb00a8117cb6c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode("utf-8", errors="ignore")
    # find lines mentioning inf.cwc.gov.in or aff.india-water.gov.in
    matches = re.findall(r'.{0,100}(?:inf\.cwc\.gov\.in|aff\.india-water\.gov\.in).{0,100}', js)
    for m in matches[:10]:
        print("MATCH:", m)
