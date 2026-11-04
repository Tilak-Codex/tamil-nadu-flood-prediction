import urllib.request
import re

url = "https://ffs.india-water.gov.in/main-es2015.fbfe583eb00a8117cb6c.js"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=15) as resp:
    js = resp.read().decode("utf-8", errors="ignore")
    # find baseUrl or environment or api
    env_matches = re.findall(r'(https?://[a-zA-Z0-9.\-_:]+(?:/[a-zA-Z0-9.\-_]+)*)', js)
    print("Found domain/URLs in main JS:")
    for u in set(env_matches):
        if any(w in u.lower() for w in ["water", "api", "cwc", "server"]):
            print("  ", u)
