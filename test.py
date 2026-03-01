import urllib.request
import re
HEADERS = {"User-Agent": "Mozilla/5.0 (F1CrawlerBot/1.0; educational project)"}
def fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.read().decode(r.headers.get_content_charset("utf-8"), errors="replace")
    except Exception as e:
        print(f"  [WARN] {url}: {e}")
        return ""
    
url = 'https://en.wikipedia.org/wiki/List_of_Formula_One_drivers'

html = fetch(url)
print(html)
