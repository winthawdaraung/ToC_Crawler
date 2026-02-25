"""
scraper.py  ─  F1 Driver Web Crawler
Scrapes Wikipedia for 100+ Formula 1 drivers using ONLY the Python
standard library (urllib) + the 're' module for all data extraction.

Run:  python scraper.py
Output: data/drivers.json
"""

import re
import urllib.request
import json
import time
import os
from datetime import date

# ────────────────────────────────────────────────────────────────────────────
#  HTTP helper
# ────────────────────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "Mozilla/5.0 (F1CrawlerBot/1.0; educational project)"}

def fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.read().decode(r.headers.get_content_charset("utf-8"), errors="replace")
    except Exception as e:
        print(f"  [WARN] {url}: {e}")
        return ""


# ────────────────────────────────────────────────────────────────────────────
#  REGULAR EXPRESSION PATTERNS
#  All data extraction uses ONLY re — no HTML parser library.
# ────────────────────────────────────────────────────────────────────────────

# RE-1  Extract driver wiki links from list / championship pages
#       Matches  href="/wiki/FirstName_LastName"  with a human-name guard
RE_DRIVER_LINK = re.compile(
    r'href="(/wiki/([A-Z][a-záéíóúàèìòùäëïöüñ\'\-]+(?:_[A-Z][a-záéíóúàèìòùäëïöüñ\'\-]+){1,3}))"',
    re.UNICODE
)

# RE-2  Full name from <title>   e.g.  "Lewis Hamilton - Wikipedia"
RE_PAGE_TITLE = re.compile(
    r'<title>\s*([A-ZÀ-Ö][a-zA-ZÀ-ö\'\-\. ]+?)\s*[-–|]',
    re.UNICODE
)

# RE-3  Date of birth 
RE_DOB = re.compile(
    r'class="bday">(\d{4}-\d{2}-\d{2})<', re.IGNORECASE
)

# RE-4  Birthplace City, Country / City, State, Country
RE_BIRTHPLACE = re.compile(
    r'class="birthplace"[^>]*>(.*?)</div>',
    re.IGNORECASE | re.DOTALL
)

# RE-5  Nationality / country flag text  e.g. "British" "Dutch" "Monégasque"
RE_NATIONALITY = re.compile(
    r'Nationality.*?</td>', 
    re.IGNORECASE | re.DOTALL
)

# RE-6  Current F1 team  e.g.  "team = [[Mercedes AMG Petronas]]"
# RE_TEAM = re.compile(
#     r'(?:team\s*=\s*(?:\{\{nowrap\|)?)\[\['
#     r'([A-Z][A-Za-z0-9\s\-&\.]+?)'
#     r'(?:\|[^\]]+)?\]\]',
#     re.IGNORECASE
# )
RE_F1_TEAM = re.compile(
    r'World Championship career.*?(?:team|Teams)</th><td[^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL
)

# RE-7  World Championship titles  — number word or digit before "World"
#       e.g. "seven-time World Champion" / "3× World Drivers' Champion"
RE_TITLES = re.compile(
    r'(?:'
        r'(?P<num>\d+)[×xX\-\s]?'
        r'|(?P<word>one|two|three|four|five|six|seven|eight|nine|ten)'
        r'[\s\-]?(?:time[\s\-])? '
    r')?'
    r"World\s+(?:Drivers['\u2019]?\s+)?Champio",
    re.IGNORECASE
)

# RE-8  Number of F1 race wins
RE_WINS = re.compile(
    r'World Championship career</th></tr>.*?Wins.*?<td[^>]*>(\d+)</td>',
    re.IGNORECASE
)

# RE-9  Car number / racing number  e.g. "car_number = 44"
RE_NUMBER = re.compile(
    r'World Championship career</th></tr>.*?Car number.*?<td[^>]*>(\d+)</td>',
    re.IGNORECASE
)

# RE-10  Podiums  e.g. "podiums = 197"
RE_PODIUMS = re.compile(
    r'World Championship career</th></tr>.*?Podiums.*?<td[^>]*>(\d+)</td>',
    re.IGNORECASE
)

# RE-11  Pole positions  e.g. "poles = 104"
RE_POLES = re.compile(
    r'World Championship career</th></tr>.*?Pole Positions.*?<td[^>]*>(\d+)</td>',
    re.IGNORECASE
)

# ────────────────────────────────────────────────────────────────────────────
#  UTILITY  —  strip HTML tags & decode entities
# ────────────────────────────────────────────────────────────────────────────

def clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&#\d+;', '', text)
    text = re.sub(r'\{\{[^}]*\}\}', '', text)   # remove wiki templates
    text = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', text)  # unwrap [[links]]
    return re.sub(r'\s+', ' ', text).strip()


# ────────────────────────────────────────────────────────────────────────────
#  PARSERS  — each uses RE results above
# ────────────────────────────────────────────────────────────────────────────

# def parse_dob(text: str) -> str:
#     m = RE_DOB.search(text)
#     if not m:
#         return "N/A"
#     if m.group("m1"):
#         return f"{m.group('m1')} {m.group('d1')}, {m.group('y1')}"
#     return f"{m.group('d2')} {m.group('m2')} {m.group('y2')}"

def parse_dob(text: str) -> str:
    """Extracts human-readable DOB (e.g., 29 July 1981) from raw HTML"""
    m = RE_DOB.search(text)
    if m:
        # group(1) captures the text after the span tags but before the next '<'
        return m.group(1).strip()
    
    # Fallback: if the bday span isn't there, look for any 'Day Month Year' pattern
    fallback = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})', text, re.IGNORECASE)
    return fallback.group(1) if fallback else "N/A"

def parse_age(dob: str) -> str:
    y = re.search(r'(?:19|20)\d{2}', dob)
    return str(date.today().year - int(y.group())) if y else "N/A"

def parse_birthplace(text: str) -> str:
    # m = RE_BIRTHPLACE.search(text)
    # return clean(m.group(1).strip()) if m else "N/A"
    m = RE_BIRTHPLACE.search(text)
    if m:
        # group(1) is "<a href="...">Stevenage</a>, Hertfordshire, England"
        raw_html = m.group(1)
        # Use your clean function to strip the <a> tags
        return clean(raw_html)
    return "N/A"

# def parse_nationality(text: str) -> str:
#     m = RE_NATIONALITY.search(text)
#     return m.group(1).strip() if m else "N/A"

def parse_nationality(text: str) -> str:
    # 1. Find the specific <td> block for Nationality
    m = RE_NATIONALITY.search(text)
    if not m:
        return "N/A"
    
    nationality_cell = m.group(0)
    
    # 2. Find all text between <a>...</a> tags in this cell
    # links= ['United Kingdom', 'British'] for Hamilton
    links = re.findall(r'<a[^>]*>([^<]+)</a>', nationality_cell)
    
    if links:
        result = links[-1].strip()
        return result
        
    return "N/A"

# def parse_team(infobox: str) -> str:
#     m = RE_TEAM.search(infobox)
#     return m.group(1).strip() if m else "N/A"
def parse_team(text: str) -> str:
    # 1. Search for the team cell after the F1 header
    m = RE_F1_TEAM.search(text)
    if not m:
        return "N/A"
    
    # This is the HTML inside the <td>...</td>
    team_cell_content = m.group(1)

    # 2. Find all text inside <a> links in this specific cell
    # Regex: r'<a[^>]*>([^<]+)</a>'
    teams = re.findall(r'<a[^>]*>([^<]+)</a>', team_cell_content)
    
    if teams:
        # Return the last one (Mercedes for Schumacher, Ferrari for Hamilton)
        return teams[-1].strip()
        
    return "N/A"

def parse_titles(text: str) -> str:
    word_map = {"one":1,"two":2,"three":3,"four":4,"five":5,
                "six":6,"seven":7,"eight":8,"nine":9,"ten":10}
    m = RE_TITLES.search(text)
    if not m:
        return "0"
    if m.group("num"):
        return m.group("num")
    if m.group("word"):
        return str(word_map.get(m.group("word").lower(), 1))
    return "1"   # matched but no number prefix → 1 title

def parse_wins(text: str) -> str:
    m = RE_WINS.search(text)
    return m.group(1) if m else "N/A"

def parse_number(text: str) -> str:
    m = RE_NUMBER.search(text)
    return m.group(1) if m else "N/A"

def parse_podiums(infobox: str) -> str:
    m = RE_PODIUMS.search(infobox)
    return m.group(1) if m else "N/A"

def parse_poles(infobox: str) -> str:
    m = RE_POLES.search(infobox)
    return m.group(1) if m else "N/A"


# ────────────────────────────────────────────────────────────────────────────
#  SCRAPE A SINGLE DRIVER PAGE
# ────────────────────────────────────────────────────────────────────────────

def parse_driver_page(url: str) -> dict:
    html = fetch(url)
    if not html:
        return {}

    # Extract infobox block for targeted regex
    ib_m = re.search(
        r'<table[^>]*class="[^"]*infobox[^"]*".*?</table>',
        html, re.DOTALL | re.IGNORECASE
    )
    infobox_html = ib_m.group(0) if ib_m else html[:8000]
    infobox_text = clean(infobox_html)

    # Full page plain text (first 12 000 chars)
    page_text = clean(html[:12000])
    # print(infobox_html)

    name_m = RE_PAGE_TITLE.search(html)
    full_name = name_m.group(1).strip() if name_m else url.split("/wiki/")[-1].replace("_", " ")

    parts = full_name.split()
    first = parts[0] if parts else full_name
    last  = " ".join(parts[1:]) if len(parts) > 1 else ""

    # dob = parse_dob(infobox_text + " " + page_text[:3000])
    dob = parse_dob(infobox_html)  # target the bday span area more specifically

    return {
        "name":        full_name,
        "first_name":  first,
        "last_name":   last,
        "dob":         dob,
        "age":         parse_age(dob),
        "birthplace":  parse_birthplace(infobox_html),
        "nationality": parse_nationality(infobox_html),
        "team":        parse_team(infobox_html),
        "titles":      parse_titles(page_text),
        "wins":        parse_wins(infobox_html),
        "podiums":     parse_podiums(infobox_html),
        "poles":       parse_poles(infobox_html),
        "number":      parse_number(infobox_html),
        "wiki_url":    url,
    }


# ────────────────────────────────────────────────────────────────────────────
#  COLLECT DRIVER LINKS FROM WIKIPEDIA LIST PAGES
# ────────────────────────────────────────────────────────────────────────────

# Pages that contain many F1 driver links
LIST_PAGES = [
    "https://en.wikipedia.org/wiki/List_of_Formula_One_drivers",
    "https://en.wikipedia.org/wiki/Formula_One_drivers_who_have_competed_in_100_or_more_Grands_Prix",   #not get used
    "https://en.wikipedia.org/wiki/List_of_Formula_One_World_Drivers%27_Champions", #not get used
]

# Known F1 driver substrings to help filter noise
F1_DRIVER_HINT = re.compile(
    r'(?:Formula[_\s]One|Grand_Prix|F1|racing_driver|Formula_1)',
    re.IGNORECASE
)

SKIP = re.compile(
    r'(Wikipedia|Category|File|Template|Help|Special|Portal|Talk|'
    r'User|Main_Page|List_of|History_of|Season|Grand_Prix_of|'
    r'Championship|Circuit|Constructors|Team_|engine|'
    r'Liberty|Formula_One|East|West|North|South)',
    re.IGNORECASE
)


def collect_driver_links(target: int = 10) -> list:
    seen, links = set(), []

    for lp in LIST_PAGES:
        if len(links) >= target:
            break
        print(f"Scanning list page: {lp}")
        html = fetch(lp)

        for m in RE_DRIVER_LINK.finditer(html):
            path = m.group(1)
            if SKIP.search(path):
                continue
            url = "https://en.wikipedia.org" + path
            if url not in seen:
                seen.add(url)
                links.append(url)
            if len(links) >= target:
                break

    return links[:target]


# ────────────────────────────────────────────────────────────────────────────
#  MAIN ENTRY POINT
# ────────────────────────────────────────────────────────────────────────────

def run_crawler(target: int = 10, out: str = "data/drivers.json"):
    os.makedirs("data", exist_ok=True)

    urls = collect_driver_links(target)
    print(f"\nFound {len(urls)} candidate driver pages. Scraping…\n")

    drivers = []
    for i, url in enumerate(urls, 1):
        print(f"  [{i:>3}/{len(urls)}] {url.split('/wiki/')[-1].replace('_',' ')}")
        d = parse_driver_page(url)
        if d and d.get("name") and len(d["name"]) > 3:
            drivers.append(d)
        print(d)
        time.sleep(0.5)   # polite crawl delay

    with open(out, "w", encoding="utf-8") as f:
        json.dump(drivers, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(drivers)} drivers to {out}")
    return drivers


if __name__ == "__main__":
    run_crawler()
