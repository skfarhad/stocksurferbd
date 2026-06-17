# Python Coding Standards

Guidelines for writing clean, maintainable Python in the `stocksurferbd` library. The library is small — favour clarity and predictable data shapes over abstraction.

---

## Core Philosophy

### Readability over cleverness
Code should read like prose. The scrapers do real work parsing messy HTML; keep the *intent* obvious even when the parsing is fiddly.

### Flat over nested
Prefer early returns and guard clauses over deep nesting. Validate inputs and check that a `find(...)` returned something, then proceed on the happy path.

### Small over large
A function should do one thing. The big "build a dict from positional table cells" blocks are the hardest part of this codebase — splitting fetch / parse / assemble / save keeps each piece testable.

### Explicit over implicit
No magic strings for URLs, table classes, market codes, or column names — name them once as constants.

---

## SOLID, lightly applied

This is a library, not a service — don't over-engineer. But the spirit still helps:

- **Single Responsibility** — separate *fetching* (HTTP), *parsing* (HTML → rows), *assembling* (rows → DataFrame), and *saving* (DataFrame → file). Today `get_company_df` mixes fetch + parse + assemble; pulling fetch into its own helper makes parsing testable against saved HTML.
- **Open/Closed** — adding a new market or data field should mean adding a method/constant, not editing a long `if/elif` chain.
- **Dependency inversion** — let callers pass in things that vary (e.g. an HTTP session, a timeout) rather than hardcoding them, so tests can inject a fixture.

Skip protocols, generics, and service-layer ceremony unless a real need appears.

---

## No magic strings — use constants

URLs, CSS class names, market codes, and output column names are repeated literals. Keep them as named constants (as `PriceData` already does for its URLs):

```python
class PriceData:
    HISTORY_URL_DSE = "https://www.dsebd.org/day_end_archive.php?endDate=<date>&archive=data"
    CURRENT_PRICE_URL_DSE = "https://www.dsebd.org/latest_share_price_scroll_l.php"
    VALID_MARKETS = ("DSE", "CSE")
```

For closed sets like market codes, define them once and reference them everywhere (validation, branching, docs).

---

## Flat code design

### Guard clauses and early returns

```python
def save_current_data(self, file_path="", file_name="...", market="DSE"):
    if market not in self.VALID_MARKETS:
        raise IOError("Invalid Stock Market! Possible values are- CSE, DSE")
    # happy path, flat
```

### Check parser results before indexing

The scrapers index into tables/rows positionally. A missing table currently surfaces as a deep `IndexError`. Guard it:

```python
table = soup.find("table", attrs={"class": EXPECTED_CLASS})
if table is None:
    raise ParseError(f"Expected table not found for {symbol}")
rows = table.find_all("tr")
```

---

## Naming conventions

### Functions: verb_noun

```python
def save_history_data(...): ...
def parse_current_prices_dse(...): ...
def get_company_df(...): ...
```

Avoid vague names like `process`, `handle`, or `do_it`.

### Classes: clear nouns

`PriceData`, `FundamentalData`, `CandlestickPlot` — good. Avoid `Manager`, `Helper`, `Utils` grab-bags.

### Variables: descriptive, no cryptic abbreviations

`latest_trading_date`, `table_rows`, `dict_list` are fine. Avoid `df1`, `tmp`, `x` for anything that lives more than a line or two.

---

## Type hints

Add type hints to public methods and shared helpers — they document the data shapes (which are easy to lose track of in scraping code) and enable IDE/`mypy` checks:

```python
def parse_float(str_val: str) -> float: ...
def save_history_data(self, symbol: str, file_path: str = "",
                      file_name: str = "history_data.xlsx", market: str = "DSE") -> None: ...
def parse_current_prices_dse(self, soup: BeautifulSoup) -> list[dict]: ...
```

---

## Data shapes

- Scraped rows are normalised to `list[dict]`, then to a `pandas.DataFrame`. Keep the dict keys / column names stable and centralised — they are the library's de-facto output schema.
- Route every numeric cell through `parse_float` / `parse_int` so types are consistent and `','`/`'--'` are handled uniformly.
- Prefer returning a `DataFrame` from the "get" layer and writing files in a thin "save" layer, so callers can use the data without round-tripping through Excel.

---

## Quick checklist

### Before every function
- [ ] Clear `verb_noun` name?
- [ ] One responsibility (not fetch + parse + save in one)?
- [ ] Type-hinted params and return?
- [ ] Inputs validated / parser results guarded before indexing?

### Before every string literal
- [ ] Is this a URL / CSS class / market code / column name that should be a constant?
- [ ] Does a constant for it already exist?

### Before committing
- [ ] No new hardcoded URLs or magic strings
- [ ] `requests.get` calls have a `timeout`
- [ ] Dead code / commented-out debug `print`s removed
- [ ] `requirements.txt` and `setup.py` pins still in sync
