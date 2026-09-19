# Feature Specification: Shariah List

**Slug:** shariah-list | **Branch:** `feature/shariah-list` | **Created:** 2026-09-19
**Status:** Implemented (2026-09-19). 107 tests pass (25 new); live CSE smoke verified 103 CSI constituents with revision and effective dates from press release #332.

## Decisions (planning interview, 2026-09-19)

| Topic | Decision |
|-------|----------|
| List frame shape | Code plus dates: `SOURCE, INDEX, TRADING_CODE, AS_OF_DATE, LIST_REVISED_DATE, LIST_EFFECTIVE_DATE`. No price columns (they overlap `PriceData`). Dates repeat per row so a saved xlsx is self-describing. |
| Revision details | Separate `get_shariah_revision_df` / `save_shariah_revision` with `CHANGE` in `ADDED / EXCLUDED / SELECTED` and `COMPANY_NAME`. `get_shariah_list_info` also returns the counts, dates and lists as a dict. |
| Unavailable source (DSE) | Registered in `SOURCES` with `fetcher=None`. Requesting it raises `IOError` explaining that DSE sells the DSES constituent list and pointing to `source='CSE'`. `list_sources()` shows `AVAILABLE=False`. |
| Release housekeeping | Version 2.0.0 -> 2.1.0, CHANGELOG entry, README usage block and schema rows, root example script `fetch_shariah_list.py`, roadmap "Shipped" entry. |

## Overview

### Objective

Add a `ShariahData` scraper that returns the standing list of Shariah-compliant
companies from a named source, starting with the CSE Shariah Index (CSI). The
source is a parameter backed by a registry so further sources are added as data
plus one parser, and every result carries the dates the list was revised and
took effect.

### Background

- **DSE** publishes the DSES index value only. The constituent list is a paid
  product (Financial Express, 2023-03-12: Tk 0.5 million one-off plus
  Tk 0.12 million per year). The only public DSES document is a 2014 image-only
  methodology brochure. Third-party DSES component pages are login-gated,
  partial or empty.
- **CSE** publishes the CSI constituents free, in two places, both verified
  live on 2026-09-19:
  1. `https://www.cse.com.bd/market/sectorindexdata` (GET). Contains the CSI
     index summary and a table headed "CSI Share by Company Name on
     September 19, 2026" with 103 rows (`SL., STOCK CODE, LTP, OPEN, HIGH,
     LOW, YCP, TRADE, VALUE(MN), VOLUME`). The page uses the same
     `id="dataTablex"` for the CSCX, CASPI, CSI and sector tables, so the CSI
     table must be located by its title text.
  2. `https://www.cse.com.bd/media/press_release` (GET). Lists releases with
     `div.media_list_title > a[href=".../media/press_release/<id>"]`. The
     semi-annual "CSE Shariah Index revised" release states the announcement
     date ("Dhaka, May 19, 2026:"), the effective date ("effective from 03 June
     2026"), the added companies, the excluded companies, and the full selected
     list with counts ("103 listed companies out of 383 listed Companies").

### Scope

In: `ShariahData` class, `SOURCES` registry (CSE implemented, DSE documented as
unavailable), list / revision / info / save methods, fixtures and tests, README,
CHANGELOG, version 2.1.0, roadmap, example script.

Out: name-to-code mapping for press-release names, historical compositions,
any DSES data, per-company screening.

---

## User Stories

See `planning/requirements.md`. In short: get the current compliant codes with
their revision dates; see the latest additions and exclusions; discover sources
and their access status; get a clear error for sources that exist but are not
publicly available.

---

## Technical Design

### Architecture Overview

```
ShariahData(HttpScraper)
├── SOURCES = {                      # registry: data, not code
│     "CSE": {market, index="CSI", list_url, revision_url, provider,
│             screening, review_cycle, access, notes, fetcher="_fetch_cse"},
│     "DSE": {market, index="DSES", ..., access="paid", fetcher=None},
│   }
├── list_sources()                   -> DataFrame (one row per source)
├── get_shariah_list_df(source)      -> DataFrame LIST_COLUMNS
├── get_shariah_revision_df(source)  -> DataFrame REVISION_COLUMNS
├── get_shariah_list_info(source)    -> dict
├── save_shariah_list(...)           -> xlsx
├── save_shariah_revision(...)       -> xlsx
│
├── _check_source(source)            # validates, resolves fetcher or raises
├── _fetch_cse()                     # GET list page + latest release
│
└── classmethod parsers (pure, fixture-testable)
    ├── parse_constituents_cse(html)     -> (as_of_date, [codes])
    ├── find_latest_revision_url_cse(html, title_keyword) -> url | None
    └── parse_revision_cse(html)         -> dict(revised_date, effective_date,
                                              added, excluded, selected,
                                              selected_count, total_listed)
```

`get_shariah_list_df` calls the source's fetcher, which returns a common
internal dict:

```python
{
  "as_of_date": date,            # trading date in the table title
  "codes": [str, ...],           # constituents (trading codes)
  "revision": {                  # None if the release could not be fetched/parsed
      "url": str,
      "revised_date": date, "effective_date": date,
      "added": [names], "excluded": [names], "selected": [names],
      "selected_count": int, "total_listed": int,
  },
}
```

The public methods shape that dict into frames, so a new source only has to
produce the same dict.

### Output schemas

| Method | Columns |
|--------|---------|
| `get_shariah_list_df` | `SOURCE`, `INDEX`, `TRADING_CODE`, `AS_OF_DATE`, `LIST_REVISED_DATE`, `LIST_EFFECTIVE_DATE` |
| `get_shariah_revision_df` | `SOURCE`, `INDEX`, `LIST_REVISED_DATE`, `LIST_EFFECTIVE_DATE`, `CHANGE` (`ADDED` / `EXCLUDED` / `SELECTED`), `COMPANY_NAME` |
| `list_sources` | `SOURCE`, `MARKET`, `INDEX`, `AVAILABLE`, `PROVIDER`, `REVIEW_CYCLE`, `ACCESS`, `LIST_URL`, `REVISION_URL`, `NOTES` |

Dates are `datetime.date`; the two list dates are `None` when the revision
release is unavailable.

### Parsing rules (CSE)

- Constituent table: the `<table>` whose first `<th>` text starts with
  `"CSI Share by Company Name"`. The date is the text after `" on "`, parsed
  with `dateutil`. Codes come from the second `<td>` of each body row (the
  anchor text); the SL. column is ignored. Missing table or date ->
  `ParseError("CSE ... layout may have changed")`.
- Latest revision link: first `div.media_list_title a` whose text contains
  `"Shariah Index revised"` (case-insensitive). The listing is newest first.
- Release body: the `div.media_list_short_details` text, whitespace-collapsed,
  entities unescaped. Regexes (case-insensitive, tolerant of `has/have`,
  `is/are`, `company/companies`, zero-padded counts and optional commas):
  - revised: `Dhaka,\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})\s*:`
  - effective: `effective\s+from\s+(\d{1,2}\s+[A-Za-z]+,?\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})`
  - added: `included (?:is|are)\s+(?P<names>.+?)\.\s+On the other hand` and
    `No new company has been included` -> `[]`
  - excluded: `i\.e\.,?\s*(?P<names>.+?),?\s+were excluded`
  - selected: `(\d+)\s+listed\s+companies\s+out\s+of\s+(\d+)\s+listed\s+companies\s+
    have\s+been\s+selected\.?\s*These\s+are[-\u2013:\s]*(.+)$` followed by the
    footer strip described below
  - Name lists split on `,` and, in the last piece only, at its first ` and `
    (company names themselves contain "and"). Every name is normalised by
    stripping surrounding whitespace and trailing `.`/`,`, so `LTD.` and `LTD`
    compare equal whether or not the name ended the sentence.
  - The selected list runs to the end of the release; a contact footer follows
    ("For detail please contact: ..." or, in #315, directly "Tania Begum
    Assistant Manager ..."). It is cut at the first footer marker, then a
    leftover person name after the sentence end is dropped unless it contains
    a company word (protects "Kohinoor Chemical Co. (BD) Ltd.").
- Any regex miss leaves that field `None`/`[]`; the method still returns.

### HTTP

Plain GETs via `HttpScraper._get`, wrapped to raise `FetchError` on
`requests.RequestException`. No CSRF. Honour `verify`/`session`/`timeout`.

### Files touched

- `stocksurferbd_pkg/stocksurferbd/shariah_data_scraper.py` (new)
- `stocksurferbd_pkg/stocksurferbd/__init__.py` (export `ShariahData`)
- `tests/fixtures/cse_sectorindexdata.html`,
  `tests/fixtures/cse_press_release_list.html`,
  `tests/fixtures/cse_press_release_332.html`,
  `tests/fixtures/cse_press_release_273.html` (new, trimmed live captures)
- `tests/conftest.py` (fixtures), `tests/test_shariah_data.py` (new)
- `fetch_shariah_list.py` (new example script)
- `README.md`, `CHANGELOG.md`, `stocksurferbd_pkg/setup.py` (2.1.0),
  `agent-os/product/roadmap.md`

---

## Acceptance Criteria

### Functional
- `get_shariah_list_df()` on the fixture: 103 rows, `AS_OF_DATE` 2026-09-19,
  `LIST_REVISED_DATE` 2026-05-19, `LIST_EFFECTIVE_DATE` 2026-06-03, first
  `AAMRANET`, last `ZAHEENSPIN`.
- `parse_revision_cse` on release #332: 3 added, 12 excluded, 103 selected,
  total 383. On release #273: 0 added, 3 excluded, 123 selected, total 384,
  effective 2024-11-25.
- `source="DSE"` raises with the paid-status message; `source="nyse"` raises
  `ValueError` listing `CSE, DSE`; `source="cse"` works (case-insensitive).
- Revision fetch failure -> list still returned, date columns `None`.

### Non-Functional
- No existing test or schema changes. New parsers are pure classmethods.

---

## Test Plan

Fixture-based, no network (mirrors `tests/test_index_data.py`):

- `test_parse_constituents_cse` (count, order, date, code sample)
- `test_parse_constituents_cse_ignores_other_tables` (CSCX/CASPI tables present)
- `test_parse_constituents_cse_missing_table` -> `ParseError`
- `test_find_latest_revision_url_cse` (skips a non-Shariah first item)
- `test_parse_revision_cse_332`, `test_parse_revision_cse_273_no_additions`
- `test_get_shariah_list_df_cse` (monkeypatched `_get` returning fixtures)
- `test_get_shariah_list_df_cse_revision_unavailable`
- `test_get_shariah_revision_df_cse`, `test_get_shariah_list_info_cse`
- `test_list_sources`, `test_unavailable_source_dse`, `test_unknown_source`

---

## Test results (2026-09-19, `pytest tests/`)

- 107 passed, 0 failed (82 pre-existing + 25 new in `tests/test_shariah_data.py`).
- Parsers additionally checked ad hoc against the live releases #250, #273,
  #292, #315 and #332: every dateline, effective date, added/excluded list and
  "N out of M" count parsed; the selected count matched `N` in all five.
- Live smoke (`ShariahData(verify=False)`): 103 CSI constituents as of
  2026-09-19, revised 2026-05-19, effective 2026-06-03, revision #332 with
  3 added / 12 excluded / 103 selected of 383; `source='DSE'` raised the
  paid-status `IOError`. Default `verify=True` failed on the CSE certificate
  chain in this environment (same as DSE, already documented in README).

## Rollout

Single PR on `feature/shariah-list`; version 2.1.0 (additive, no breaking
change). Manual smoke against the live CSE site before merge.
