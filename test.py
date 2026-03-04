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

# RE_TABLE = re.compile(r'<table class=wikitable sortable sticky-header.*>(.*?)</table>', re.DOTALL)
RE_TABLE = re.compile(r'<table class="wikitable sortable sticky-header[^"]*"[^>]*>(.*?)</table>', re.DOTALL)
html = fetch(url)
table = RE_TABLE.search(html).group(1)
# print(table)
# print(html)
def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text).strip()
    text = re.sub(r'a?&[#0-9]+;', '', text)
    return text

rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL)
header = re.findall(r'<th[^>]*>(.*?)</th>', rows[0], re.DOTALL)
header = [clean_text(cell) for cell in header]
print(header)

for row in rows[1:]:
    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
    cells = [clean_text(cell) for cell in cells]
    if len(cells) == len(header):
        driver = dict(zip(header, cells))
        # print(driver)
