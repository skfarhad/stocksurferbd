# Error Handling Standards

Error handling for `stocksurferbd`'s scrapers — the two failure modes that matter are **network failures** (the DSE/CSE site is down, slow, or refuses the request) and **parse failures** (the page loaded but its HTML layout changed or a symbol returned no data).

---

## General Principles

- **Fail clearly, with the symbol/market in the message.** A user running over hundreds of symbols needs to know exactly which one failed and why. The fundamentals scraper already does this: `raise Exception(f"Data fetch error for: {symbol}")`.
- **Distinguish network errors from parse errors.** They have different fixes (retry vs. update the parser). Prefer typed exceptions over bare `Exception`.
- **Don't let one bad symbol abort a batch.** Batch drivers should catch per-symbol, log, and continue (as `fetch_company_data.py` does).
- **Set request timeouts.** `requests.get(...)` without a timeout can hang forever; always pass `timeout=`.

---

## Suggested Exception Types

Bare `Exception` is used today; prefer a small hierarchy so callers can react:

```python
class StockSurferError(Exception):
    """Base error for the library."""

class FetchError(StockSurferError):
    """Network/HTTP failure fetching a source page."""

class ParseError(StockSurferError):
    """Page fetched, but expected table/field was missing or malformed."""
```

---

## Fetch Pattern

```python
def _get(self, url):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"Failed to fetch {url}: {e}") from e
    return resp
```

- Catch `requests.RequestException` (covers timeouts, connection errors, HTTP errors via `raise_for_status`).
- Wrap in `FetchError` so callers don't need to import `requests`.
- Optionally retry transient failures with simple backoff before giving up.

---

## Parse Pattern

The scrapers locate tables by CSS class and index into rows/cells positionally. When a layout changes, those lookups return `None` or raise `IndexError` deep in a comprehension. Guard the boundaries:

```python
table = soup.find("table", attrs={"class": EXPECTED_CLASS})
if table is None:
    raise ParseError(f"Expected table not found for {symbol} — page layout may have changed")
```

- Check that `find(...)` returned something before using it.
- Validate row/column counts before indexing, so the error names the problem instead of surfacing a raw `IndexError`.
- Treat `'--'` / empty cells as missing data and normalise them (the `parse_float`/`parse_int` helpers already map `'--'` → `0`) — but be deliberate about whether `0` or "missing" is the right value for the field.

---

## Batch Driver Pattern

```python
for symbol in symbols:
    try:
        loader.save_company_data(symbol, path="company_info")
    except StockSurferError as e:
        print(f"Skipping {symbol}: {e}")
```

- Catch the library's base error, report it, and keep going.
- Don't swallow `KeyboardInterrupt` / `SystemExit` — only catch `StockSurferError` (or `Exception` as a last resort, but log it).
