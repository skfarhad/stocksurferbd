# Task Breakdown: Shariah List

**Spec**: `2026-09-19-shariah-list`
**Status**: Implemented and tested (2026-09-19): 110 passed / 0 failed (82 existing + 28 new), shariah_data_scraper.py at 100% coverage; live CSE smoke passed (103 constituents, revision #332 parsed)

Adds `ShariahData`, a source-parameterised scraper for Shariah-compliant
company lists. CSE (CSI) is the only implemented source; DSE (DSES) is
registered as unavailable. Nothing existing changes. Tests run offline against
fixtures under `tests/fixtures/`; run with `pytest tests/` from the repo root.

## Task List

### Task Group 1: Fixtures and test scaffolding

**Priority**: High
**Files**:
- `tests/fixtures/cse_sectorindexdata.html` (new)
- `tests/fixtures/cse_press_release_list.html` (new)
- `tests/fixtures/cse_press_release_332.html` (new)
- `tests/fixtures/cse_press_release_273.html` (new)
- `tests/conftest.py`

#### Subtasks:

**1.1 Constituent page fixture**
- [x] Capture `https://www.cse.com.bd/market/sectorindexdata` (GET, `verify=False` if the cert chain fails) and trim to the `<table id="dataTablex">` blocks only, wrapped in minimal `<html><body>`. Keep the CSCX and CASPI tables and the "Eligibility Criteria" paragraph so table selection by title is exercised; keep all 103 CSI rows.
- [x] Confirm the CSI title cell reads `CSI Share by Company Name on September 19, 2026`.

**1.2 Press-release fixtures**
- [x] `cse_press_release_list.html`: trim the listing to three `div.mediareport_box` items: one non-Shariah item first (#333, "Commodity Derivatives Insights" book), then #332 "CSE Shariah Index revised", then one older Shariah item (#315). Keep `div.media_list_title` anchors and `div.floatleft` date cells.
- [x] `cse_press_release_332.html`: trim release #332 to its `div.mediareport_box` (title, `div.media_list_short_details` body, date cell). Keep the full "These are- ..." list and the "For detail please contact" footer so the end-of-list regex is tested.
- [x] `cse_press_release_273.html`: same trim for release #273 ("No new company has been included", 3 excluded, 123 of 384, effective November 25, 2024).

**1.3 conftest loaders**
- [x] Add `cse_sectorindexdata_html`, `cse_press_release_list_html`, `cse_press_release_332_html`, `cse_press_release_273_html` text fixtures under the existing "CSE fixtures" section.

**Acceptance Criteria**:
- All four files load as UTF-8; none exceeds ~150 KB.
- The trimmed constituent page still contains three `dataTablex` tables plus the sector table.

---

### Task Group 2: ShariahData scraper (registry, parsers, public API)

**Priority**: High
**Files**:
- `stocksurferbd_pkg/stocksurferbd/shariah_data_scraper.py` (new)
- `stocksurferbd_pkg/stocksurferbd/__init__.py`

#### Subtasks:

**2.1 Module docstring and registry**
- [x] Module docstring summarising the sources landscape (DSE paid, CSE free, third parties partial) with the verification date 2026-09-19.
- [x] `class ShariahData(HttpScraper)` with `SOURCES` dict. Entry keys: `market`, `index`, `list_url`, `revision_url`, `provider`, `screening`, `review_cycle`, `access`, `notes`, `fetcher` (method name or `None`). Entries: `"CSE"` (fetcher `"_fetch_cse"`) and `"DSE"` (fetcher `None`, access `"paid"`, notes citing the Financial Express 2023-03-12 fee figures and the 2014 methodology PDF).
- [x] Inline comments on each registry field and each source entry explaining where the data comes from and what the dates mean (as-of trading date vs. revision announcement date vs. effective date).
- [x] Column constants: `LIST_COLUMNS`, `REVISION_COLUMNS`, `SOURCES_COLUMNS`; `CHANGE_ADDED = "ADDED"`, `CHANGE_EXCLUDED = "EXCLUDED"`, `CHANGE_SELECTED = "SELECTED"`; `REVISION_TITLE_KEYWORD_CSE = "Shariah Index revised"`; `CONSTITUENT_TITLE_CSE = "{index} Share by Company Name"`.

**2.2 Source validation**
- [x] `_check_source(cls, source)`: strip/upper; unknown -> `ValueError("Unknown Shariah source ...; choose from CSE, DSE")`; `fetcher is None` -> `IOError` quoting the entry's `notes` and pointing to `source='CSE'`. Returns `(name, entry)`.
- [x] `list_sources(cls)` -> `DataFrame[SOURCES_COLUMNS]` with `AVAILABLE = fetcher is not None`.

**2.3 CSE parsers (pure classmethods)**
- [x] `parse_constituents_cse(html) -> (as_of_date, codes)`: iterate `<table>`s, pick the one whose first `<th>` text starts with `CONSTITUENT_TITLE_PREFIX_CSE`; parse the date after `" on "` with `dateutil`; codes = second `<td>` text of each `<tbody>` row, stripped/uppercased, skipping blanks. `ParseError` if no table or no date.
- [x] `find_latest_revision_url_cse(html) -> str | None`: first `div.media_list_title a` whose text contains `REVISION_TITLE_KEYWORD_CSE` (case-insensitive); return its `href`.
- [x] `parse_revision_cse(html) -> dict`: locate `div.media_list_short_details` (fallback: whole body text); collapse whitespace, unescape entities; apply the regexes from the spec for `revised_date`, `effective_date`, `added`, `excluded`, `selected`, `selected_count`, `total_listed`. `_split_names(text)` splits on `,` and a final ` and `, strips whitespace and trailing `.`/`,` from every name, drops empties. Missing pieces -> `None` / `[]`. `ParseError` only when the details block itself is missing.

**2.4 CSE fetcher**
- [x] `_get_text(url)` helper wrapping `self._get(url).raise_for_status()` in `FetchError`.
- [x] `_fetch_cse()`: GET `list_url` -> `parse_constituents_cse`; then try GET `revision_url` -> `find_latest_revision_url_cse` -> GET release -> `parse_revision_cse`, adding `"url"`. Any `StockSurferError` in the revision branch is caught, printed as a warning, and `revision` is set to `None`. Return `{"as_of_date", "codes", "revision"}`.

**2.5 Public API**
- [x] `_load(source)` -> `(name, entry, data)` dispatching to `getattr(self, entry["fetcher"])()`.
- [x] `get_shariah_list_df(source="CSE")` -> `DataFrame[LIST_COLUMNS]`, one row per code, dates from `revision` or `None`.
- [x] `get_shariah_revision_df(source="CSE")` -> `DataFrame[REVISION_COLUMNS]`; rows in order ADDED, EXCLUDED, SELECTED; empty frame with columns when `revision` is `None`.
- [x] `get_shariah_list_info(source="CSE")` -> dict merging the registry entry (minus `fetcher`) with `as_of_date`, `constituent_count`, `list_revised_date`, `list_effective_date`, `total_listed`, `added`, `excluded`, `selected_count`, `revision_announcement_url`.
- [x] `save_shariah_list(file_path="", file_name="shariah_list.xlsx", source="CSE")` and `save_shariah_revision(file_path="", file_name="shariah_revision.xlsx", source="CSE")` via `to_excel(index=False)`.
- [x] Export `ShariahData` from `__init__.py`.

**Acceptance Criteria**:
- Parsers are classmethods with no network access.
- `get_shariah_list_df()` works with only the constituent page when the release is unreachable.
- Every registry entry and every parser has comments naming its source URL and what each date means.

---

### Task Group 3: Tests

**Priority**: High
**Files**:
- `tests/test_shariah_data.py` (new)

#### Subtasks:

**3.1 Parser tests**
- [x] `test_parse_constituents_cse`: 103 codes, `as_of_date == date(2026, 9, 19)`, first `AAMRANET`, last `ZAHEENSPIN`, all unique and uppercase.
- [x] `test_parse_constituents_cse_ignores_other_tables`: no CSCX/CASPI codes leak in (e.g. the count equals the CSI table row count, not the sum).
- [x] `test_parse_constituents_cse_missing_table` -> `ParseError`.
- [x] `test_find_latest_revision_url_cse`: returns the #332 URL, skipping the non-Shariah first item.
- [x] `test_find_latest_revision_url_cse_none` on HTML without a match.
- [x] `test_parse_revision_cse_332`: revised 2026-05-19, effective 2026-06-03, 3 added (first `ASIATIC LABORATORIES LIMITED`), 12 excluded (contains `GRAMEENPHONE LIMITED`), 103 selected, total 383, last selected `ZAHEEN SPINNING PLC` (trailing period normalised away).
- [x] `test_parse_revision_cse_273_no_additions`: 0 added, 3 excluded, 123 selected, total 384, effective 2024-11-25.
- [x] `test_parse_revision_cse_missing_block` -> `ParseError`.

**3.2 Public API tests (monkeypatched HTTP)**
- [x] Helper that patches `loader._get` to return fixture text by URL (list page, listing, release #332).
- [x] `test_get_shariah_list_df_cse`: columns `== LIST_COLUMNS`, 103 rows, `SOURCE == "CSE"`, `INDEX == "CSI"`, dates populated.
- [x] `test_get_shariah_list_df_cse_revision_unavailable`: `_get` raises for the listing URL -> 103 rows, date columns all `None`.
- [x] `test_get_shariah_revision_df_cse`: `CHANGE` value counts `{ADDED: 3, EXCLUDED: 12, SELECTED: 103}`.
- [x] `test_get_shariah_list_info_cse`: keys and counts.
- [x] `test_save_shariah_list_writes_xlsx` (tmp_path).
- [x] `test_list_sources`: two rows, `AVAILABLE` is `[True, False]` for `CSE, DSE`.
- [x] `test_unavailable_source_dse` -> `IOError` mentioning `CSE`.
- [x] `test_unknown_source` -> `ValueError`; `source="cse"` accepted.

**Acceptance Criteria**:
- New tests pass; the existing 82 tests still pass (`pytest tests/`).
- Result (2026-09-19): 110 passed, 0 failed; `shariah_data_scraper.py` 100% statement coverage, package 77%.

---

### Task Group 4: Docs, version, example script, roadmap

**Priority**: Medium
**Files**:
- `README.md`
- `CHANGELOG.md`
- `stocksurferbd_pkg/setup.py`
- `fetch_shariah_list.py` (new)
- `agent-os/product/roadmap.md`

#### Subtasks:

**4.1 README**
- [x] Add "#### Downloading the Shariah-compliant company list (CSE: CSI)-" usage block after the index section: `save_shariah_list`, `save_shariah_revision`, `get_shariah_list_df`, `get_shariah_list_info`, `list_sources`.
- [x] Add a callout explaining why DSE is not a source (paid DSES list) and that CSI is a close but not identical proxy.
- [x] Add schema rows under "Output data schema" for `save_shariah_list` and `save_shariah_revision`.
- [x] Mention `ShariahData` in the description line at the top.

**4.2 CHANGELOG and version**
- [x] `## [2.1.0] - 2026-09-19` with an "Added" section describing `ShariahData`, the registry and the DSE status.
- [x] `setup.py` version `2.1.0`.

**4.3 Example script**
- [x] `fetch_shariah_list.py`: saves `cse_shariah_list.xlsx` and `cse_shariah_revision.xlsx`, prints `get_shariah_list_info()` summary.

**4.4 Roadmap**
- [x] Add "8. [x] Shariah-compliant company list (2.1.0, 2026-09-19)" to Shipped with the spec path.

**Acceptance Criteria**:
- README example is copy-paste runnable against the live site.

---

## Execution Order

1. **Fixtures and test scaffolding** (captures live pages once; everything else is offline)
2. **ShariahData scraper**
3. **Tests**
4. **Docs, version, example script, roadmap**

---

## Key Implementation Notes

### Patterns to Follow
- Mirror `IndexData`: class-level URL/column constants, pure `parse_*` classmethods, thin `get_*_df` / `save_*` wrappers, `_check_*` validators raising `ValueError` / `IOError`.
- Use `FetchError` / `ParseError` from `utils.py`; never let a `requests` exception or `AttributeError` surface.
- Locate tables by header text, not by CSS id (the CSE page repeats `id="dataTablex"`).
- Keep `black`-compatible formatting and 4-space indentation.

### Risk Mitigation
- Press-release wording drifts between releases. The regexes are tested on two differently worded releases (#332 and #273), and every field degrades to `None` / `[]` rather than failing the list.
- The CSE certificate chain may fail in some environments; the class inherits `verify=` from `HttpScraper`.
- The constituent table's title date is a trading date, not the revision date. Comments and README make the three dates explicit.

---

## Dependencies

**External Dependencies:**
- None new. `requests`, `beautifulsoup4`, `pandas`, `python-dateutil` already pinned.

**Internal Dependencies:**
- `HttpScraper`, `FetchError`, `ParseError` in `utils.py` (unchanged).
