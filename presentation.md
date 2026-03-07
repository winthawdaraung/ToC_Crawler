# F1 Driver Crawler — Presentation Script
**YouTube Presentation Guide (~10 minutes)**

---

## SLIDE 1 — Title Slide (0:00–0:30)

**Show on screen:**
- Project title: "F1 Driver Database Crawler"
- Your name + course
- Live site URL (Render.com link)

**Say:**
> "Hi, I'm [name]. Today I'll walk you through my F1 Driver Crawler —
> a web scraping application that extracts Formula 1 driver data from
> Wikipedia using ONLY Python's standard library and regular expressions,
> then serves it through a Flask web application."

---

## SLIDE 2 — Project Overview (0:30–1:30)

**Show on screen:**
```
INPUT                    PROCESS                  OUTPUT
─────────────────────────────────────────────────────────
Wikipedia List Pages  →  Python RE scraper    →  drivers.json
(3 pages)                (12 regex patterns:       (150 drivers)
                          RE-0 through RE-11)
                      →  Flask web app        →  Live website
                      →  Vanilla JS filter    →  REST API
```

**Say:**
> "The project has three layers:
> 1. A scraper that crawls Wikipedia for 150+ F1 drivers
> 2. A Flask backend that serves the data
> 3. A frontend with live search and filtering
>
> The key constraint: NO BeautifulSoup, NO Scrapy —
> all data extraction is done purely with regular expressions.
> The scraper defines 12 compiled regex patterns, RE-0 through RE-11,
> each responsible for extracting a specific piece of driver data."

---

## SLIDE 3 — Project File Structure (1:30–2:00)

**Show on screen (open VS Code):**
```
ToC_Crawler/
├── scraper.py          ← core crawler (12 regex patterns: RE-0 to RE-11)
├── app.py              ← Flask routes + API
├── data/drivers.json   ← generated output
├── templates/
│   ├── index.html      ← driver list table
│   └── driver.html     ← driver detail page
├── static/
│   ├── css/style.css   ← F1 dark theme
│   └── js/main.js      ← client-side filter
├── requirements.txt
├── render.yaml         ← deployment config
└── Procfile
```

**Say:**
> "Here's the project structure. scraper.py is the heart of the project.
> Let me walk you through the most important regular expressions."

---

## SLIDE 4 — RE-0: Table Extraction (2:00–2:30)

**Show on screen (scraper.py):**
```python
# RE-0  Extract table from list / championship pages
RE_TABLE = re.compile(
    r'<table class="wikitable sortable sticky-header[^"]*"[^>]*>(.*?)</table>',
    re.DOTALL
)
```

**Explain each part on screen:**
```
<table                          ← match opening table tag
  class="wikitable sortable     ← Wikipedia's standard data table classes
  sticky-header                 ← the specific class on F1 driver list tables
  [^"]*"                        ← allow any extra classes after (e.g. "jquery-tablesorter")
  [^>]*>                        ← skip any other attributes on the tag
  (.*?)                         ← CAPTURE the entire table contents (lazy)
</table>                        ← stop at closing tag

re.DOTALL                       ← makes . match newlines (table spans many lines)
```

**Usage in code:**
```python
# In collect_driver_links():
table = RE_TABLE.search(html).group(1) if RE_TABLE.search(html) else html

# In fallback_data_from_list():
table = RE_TABLE.search(html).group(1) if RE_TABLE.search(html) else html
```

**Say:**
> "RE-0 is the entry point of the entire scraper.
> Before we can find any driver links, we first need to isolate
> the correct HTML table from the Wikipedia list page —
> because each page contains many tables: navigation, sidebars, footers.
>
> The pattern targets the exact CSS classes Wikipedia uses
> for its sortable data tables: 'wikitable sortable sticky-header'.
> The `[^"]*` part is important — it allows for extra dynamically
> added classes like 'jquery-tablesorter' without breaking the match.
>
> re.DOTALL is essential here because the table spans hundreds
> of HTML lines, and without it the dot would not match newlines."

---

## SLIDE 5 — RE-1: Driver Link Extraction (2:30–4:00)
### MOST IMPORTANT — Show this in detail

**Show on screen (scraper.py):**
```python
RE_DRIVER_LINK = re.compile(
    r'href="(/wiki/([A-Z][a-záéíóúàèìòùäëïöüñ\'\-]+'
    r'(?:_[A-Z][a-záéíóúàèìòùäëïöüñ\'\-]+){1,3}))"',
    re.UNICODE
)
```

**Explain each part on screen:**
```
href="(                     ← literal href attribute opening
  /wiki/                    ← must be a Wikipedia article path
  (                         ← start capturing the name
    [A-Z]                   ← first letter MUST be uppercase
    [a-záéíóú...'\-]+       ← rest of first name (includes accents!)
    (?:                     ← non-capturing group for more name parts
      _[A-Z]                ← underscore + capital (e.g. _Hamilton)
      [a-záéíóú...'\-]+     ← rest of word
    ){1,3}                  ← 1 to 3 more name parts
  )
)"                          ← closing href quote
```

**Say:**
> "RE-1 is responsible for finding driver links from the extracted table.
> What makes it complex:
> - It enforces Title Case — each word starts with uppercase
> - It supports international characters like á, é, ü for drivers like
>   Räikkönen or Pérez
> - The {1,3} quantifier means it matches 2 to 4 word names
> - This filters out non-person links like /wiki/Formula_One or /wiki/2024_season"

---

## 🎬 SLIDE 5 — RE-2 & RE-3: Name and DOB Extraction (3:30–4:30)

**Show on screen:**
```python
# RE-2: Extract driver name from page title
RE_PAGE_TITLE = re.compile(
    r'<title>\s*([A-ZÀ-Ö][a-zA-ZÀ-ö\'\-\. ]+?)\s*[-–|]',
    re.UNICODE
)
# Matches: <title>Lewis Hamilton - Wikipedia</title>
# Returns: "Lewis Hamilton"

# RE-3: Date of birth from HTML span
RE_DOB = re.compile(
    r'class="bday">(\d{4}-\d{2}-\d{2})<',
    re.IGNORECASE
)
# Matches: <span class="bday">1985-01-07</span>
# Returns: "1985-01-07"
```

**Say:**
> "RE-2 extracts the driver's full name from the HTML title tag.
> The lazy `+?` quantifier stops at the first dash or pipe —
> so 'Lewis Hamilton - Wikipedia' gives us just 'Lewis Hamilton'.
>
> RE-3 targets Wikipedia's standard bday CSS class
> which always formats dates as YYYY-MM-DD —
> making this a very reliable extraction."

---

## SLIDE 6 — RE-4 & RE-5: Birthplace & Nationality (4:30–5:15)

**Show on screen:**
```python
# RE-4: Birthplace
RE_BIRTHPLACE = re.compile(
    r'class="birthplace"[^>]*>(.*?)<\/span>',
    re.IGNORECASE | re.DOTALL
)
# Matches: <span class="birthplace">Stevenage, England</span>
# Returns: "Stevenage, England"

# RE-5: Nationality
RE_NATIONALITY = re.compile(
    r'Nationality.*?</td>',
    re.IGNORECASE | re.DOTALL
)
# Matches the entire Nationality table cell
# clean() then strips the HTML tags from the result
```

**Say:**
> "RE-4 uses `[^>]*` to skip any extra HTML attributes on the span tag,
> then `.*?` with DOTALL to lazily capture the birthplace text —
> even if it spans multiple lines in the HTML.
>
> RE-5 uses DOTALL because the nationality cell in Wikipedia's
> infobox spans multiple HTML lines with flag icons."

---

## SLIDE 7 — RE-6 to RE-11: Career Stats + SKIP & F1_DRIVER_HINT (5:15–6:00)

**Show on screen:**
```python
# RE-6: Current team — anchors on "World Championship career" header
RE_F1_TEAM = re.compile(
    r'World Championship career.*?(?:team|Teams)</th><td[^>]*>(.*?)</td>',
    re.IGNORECASE | re.DOTALL
)

# RE-7 to RE-11: All stats follow the same anchor pattern:
# "World Championship career" → find the stat row → capture digits
RE_TITLES  = re.compile(r'World Championship career</th></tr>.*?Championships.*?<td[^>]*>(\d+)', re.IGNORECASE)
RE_WINS    = re.compile(r'World Championship career</th></tr>.*?Wins.*?<td[^>]*>(\d+)', re.IGNORECASE)
RE_NUMBER  = re.compile(r'World Championship career</th></tr>.*?Car number.*?<td[^>]*>(\d+)', re.IGNORECASE)
RE_PODIUMS = re.compile(r'World Championship career</th></tr>.*?Podiums.*?<td[^>]*>(\d+)', re.IGNORECASE)
RE_POLES   = re.compile(r'World Championship career</th></tr>.*?Pole Positions.*?<td[^>]*>(\d+)', re.IGNORECASE)

# SKIP: filters out non-driver Wikipedia pages during link collection
SKIP = re.compile(
    r'(Wikipedia|Category|File|Template|List_of|Season|Grand_Prix_of|Circuit)',
    re.IGNORECASE
)
```

**Say:**
> "RE-6 through RE-11 all use the same structural anchor —
> 'World Championship career' — to find the right section of
> the infobox table before capturing the stat digit.
> This is robust because Wikipedia's infobox structure is consistent.
>
> The SKIP pattern is also important — it filters out
> thousands of non-driver links like Category pages,
> Season articles, and Circuit pages during link collection,
> leaving only real driver name URLs."

---

## SLIDE 8 — clean() Function + inline re. calls (6:00–6:30)

**Show on screen:**
```python
def clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)          # strip HTML tags
    text = re.sub(r'&amp;', '&', text)             # decode &amp;
    text = re.sub(r'&nbsp;', ' ', text)            # decode &nbsp;
    text = re.sub(r'&#\d+;', '', text)             # numeric entities
    text = re.sub(r'\{\{[^}]*\}\}', '', text)      # {{wiki templates}}
    text = re.sub(r'\[\[([^\]|]*\|)?([^\]]*)\]\]', r'\2', text)  # unwrap [[links]]
    return re.sub(r'\s+', ' ', text).strip()       # collapse whitespace
```

**Say:**
> "The clean() function uses 7 regex substitutions to turn messy
> Wikipedia HTML into plain readable text.
> The last pattern is the most interesting — it unwraps Wikipedia's
> double bracket link syntax: [[Lewis Hamilton|Hamilton]] becomes Hamilton,
> using a backreference \\2 to keep only the display text."

---

## SLIDE 9 — Live Demo (6:30–8:30)

**Show on screen (switch to browser):**

1. Open the live Render.com URL
2. Show the full driver table loading
3. Type "hamilton" in search box → show instant JS filtering
4. Select "British" from nationality dropdown
5. Select "Mercedes" from team dropdown
6. Click on Lewis Hamilton → show detail page
7. Open browser DevTools → Network tab → show no API calls during filter
8. Open `https://yourapp.render.com/api/drivers?q=verstappen`
9. Open `https://yourapp.render.com/api/stats`

**Say:**
> "Here's the live application deployed on Render.com.
> Notice the filtering happens instantly with no page reload —
> that's the client-side JavaScript reading the data-* attributes
> that Flask baked into the HTML at render time.
> The API endpoints allow programmatic access to the same data."

---

## SLIDE 10 — Architecture Summary (8:30–9:30)

**Show on screen:**
```
┌─────────────────────────────────────────┐
│           DATA LAYER                     │
│  scraper.py ──► data/drivers.json        │
│  12 regex patterns (RE-0 to RE-11)       │
└──────────────────┬──────────────────────┘
                   │ json.load()
┌──────────────────▼──────────────────────┐
│           BACKEND  (app.py)              │
│  /          → index page                 │
│  /driver/   → detail page                │
│  /api/drivers → filtered JSON            │
│  /api/stats   → aggregated stats         │
└──────────────────┬──────────────────────┘
                   │ HTML + data-* attrs
┌──────────────────▼──────────────────────┐
│           FRONTEND                       │
│  Jinja2 templates + CSS + vanilla JS     │
│  filterDrivers() — zero server calls     │
└─────────────────────────────────────────┘

Deployed on: Render.com
Config:      render.yaml (auto-deploy on git push)
```

**Say:**
> "To summarise the architecture:
> The scraper runs once at deploy time and saves to JSON.
> Flask reads that JSON and serves it through 4 routes.
> The frontend filters client-side using data attributes — 
> no extra server round trips needed.
> The whole thing deploys automatically via render.yaml
> whenever I push to GitHub."

---

## SLIDE 11 — Conclusion (9:30–10:00)

**Show on screen:**
```
What was achieved:
   • 150+ F1 drivers scraped from Wikipedia
   • 12 regex patterns (RE-0 to RE-11) for data extraction
   • Zero third-party scraping libraries
   • REST API with filtering
   • Deployed live on Render.com

Technologies:
   • Python stdlib only (urllib + re + json)
   • Flask + Jinja2
   • Vanilla JavaScript
   • Gunicorn + Render.com
```

**Say:**
> "In summary, this project demonstrates how powerful Python's
> built-in re module is for web scraping without any third-party libraries.
> 12 compiled regex patterns, RE-0 through RE-11, handle everything
> from link discovery to structured data extraction across 150 F1 driver pages.
> Thank you for watching — the live link and source code are in the description."

---

## Timing Summary

| Slide | Topic | Time | Duration |
|-------|-------|------|----------|
| 1 | Title | 0:00 | 0:30 |
| 2 | Overview | 0:30 | 1:00 |
| 3 | File structure | 1:30 | 0:30 |
| 4 | RE-1 Driver links ⭐ | 2:00 | 1:30 |
| 5 | RE-2 & RE-3 Name/DOB | 3:30 | 1:00 |
| 6 | RE-4 & RE-5 Birthplace/Nat | 4:30 | 0:45 |
| 7 | RE-6 to RE-11 Stats | 5:15 | 0:45 |
| 8 | clean() function | 6:00 | 0:30 |
| 9 | Live demo 🎥 | 6:30 | 2:00 |
| 10 | Architecture | 8:30 | 1:00 |
| 11 | Conclusion | 9:30 | 0:30 |

---

## Before Recording Checklist

- [ ] App is live on Render.com and loading correctly
- [ ] `data/drivers.json` has 100+ drivers
- [ ] Browser zoom set to 125% so code is readable
- [ ] VS Code font size increased (Ctrl+= )
- [ ] Terminal shows `(venv)` prompt
- [ ] Close Slack/notifications before recording
- [ ] Test microphone audio levels
- [ ] Have scraper.py open in VS Code on the RE patterns section