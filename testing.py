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
# url = "https://en.wikipedia.org/wiki/Ernesto_Brambilla"
# url = "https://en.wikipedia.org/wiki/Johnny_Cecotto"
# url = 'https://en.wikipedia.org/wiki/Edgar_Barth'
# url = ''
# html = fetch(url)

# print(html)

# ib_stats = re.search(
#         r'<table[^>]*class="[^"]*infobox[^"]*".*?World Championship career.*?(?:(?:</table>).*?</table>|</table>)',
#         html, re.DOTALL | re.IGNORECASE
#     )

# print(ib_stats.group(0))    

# RE_TITLES = re.compile(
#     r'World Championship career</th></tr>.*?Championships.*?<td[^>]*>(\d+)',
#     re.IGNORECASE
# )

# m = RE_TITLES.search(ib_stats.group(0))
# print(m.group(1))

# RE_WINS = re.compile(
#     r'World Championship career</th></tr>.*?Wins.*?<td[^>]*>(\d+)</td>',
#     re.IGNORECASE
# )

# m = RE_WINS.search(ib_stats.group(0))
# print(m.group(1))

# RE_POLES = re.compile(
#     r'World Championship career</th></tr>.*?Pole Positions.*?<td[^>]*>(\d+)</td>',
#     re.IGNORECASE
# )

# def parse_poles(infobox: str) -> str:
#     m = RE_POLES.search(infobox)
#     return m.group(1) if m else "N/A"

# print(parse_poles(ib_stats.group(0)))


url = 'https://en.wikipedia.org/wiki/Lewis_Hamilton'

html = fetch(url)



def parse_number(text: str) -> str:
    m = RE_NUMBER.search(text)
    return m.group(1) if m else "N/A"

RE_NUMBER = re.compile(
    r'World Championship career</th></tr>.*?Car number.*?<td[^>]*>(\d+)</td>',
    re.IGNORECASE
)
ib_stats = re.search(
        r'<table[^>]*class="[^"]*infobox[^"]*".*?World Championship career.*?(?:(?:</table>).*?</table>|</table>)',
        html, re.DOTALL | re.IGNORECASE
    )
print(ib_stats.group(0))
# print(parse_number(ib_stats.group(0)))
