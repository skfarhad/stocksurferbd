# Validation Standards

Input validation for `stocksurferbd`. The library's inputs are small and well-defined — stock symbols, market codes, file paths, and plotting parameters — so validation is about catching bad arguments early with a clear message, not heavy schema work.

---

## General Principles

- Validate arguments at the public method boundary, before any network call.
- Fail with a specific, actionable message that names the bad argument and the allowed values.
- Keep allowed values in one place (constants), not retyped per check.

---

## Market Code

Only `'DSE'` and `'CSE'` are valid. The library already enforces this — keep doing so for every market-taking method:

```python
VALID_MARKETS = ("DSE", "CSE")

if market not in VALID_MARKETS:
    raise IOError("Invalid Stock Market! Possible values are- CSE, DSE")
```

Prefer comparing against the shared constant rather than literals, and accept case-insensitively if convenient (`market.upper()`).

---

## Symbol

- Require a non-empty string; strip whitespace and upper-case it before building the URL.
- Don't assume the symbol exists — an unknown symbol returns a page without the expected tables, which should surface as a `ParseError` (see error-handling), not a confusing `IndexError`.

```python
if not symbol or not symbol.strip():
    raise ValueError("symbol must be a non-empty string")
symbol = symbol.strip().upper()
```

---

## File Paths

- `save_*` methods take a directory/file name. Ensure the target directory exists (or create it) before writing, so `to_excel` doesn't fail with an opaque error.
- Use `os.path.join` for portability (already done).

---

## Plotting Parameters (`CandlestickPlot.show_plot`)

- `data_n`: positive integer (number of recent points to plot).
- `resample`: boolean.
- `step`: only meaningful when `resample=True`; expect a pandas offset string like `'3D'`, `'7D'`. Validate the format and ignore/warn if `resample=False`.

```python
if data_n <= 0:
    raise ValueError("data_n must be a positive integer")
if resample and not step:
    raise ValueError("step is required when resample=True (e.g. '3D', '7D')")
```

---

## Data-cell normalisation

Scraped cells use `','` thousands separators and `'--'` for missing values. The `parse_float`/`parse_int` helpers normalise these. When adding new fields, route every numeric cell through these helpers so output types stay consistent, and decide explicitly whether a missing value should become `0` or be left blank.
