# Feature Requirements: Bulk date-range news scraper

## Overview
`FundamentalData.get_news_df(symbol)` fetches news one HTTP request per company
(`criteria=3`, `inst=<symbol>`). A consumer wanting the whole market makes ~400
requests — slow and failure-prone. DSE's `old_news.php` supports a date-range mode
(`criteria=4`, empty `inst`) that returns every symbol's news in a single request.
This feature adds a `get_all_news_df(start_date, end_date)` method that uses it.

## User Stories
- As a market-wide consumer (e.g. MarketWiki BD `sync_news`), I want one range call
  that returns all symbols' news, so that I replace ~400 per-symbol requests per run.

## Functional Requirements
1. Add `FundamentalData.get_all_news_df(self, start_date, end_date)` returning a
   DataFrame `[symbol, date, title, news]`, newest first.
2. Build the URL in date-range mode: `criteria=4`, `startDate`, `endDate`, empty
   `inst`. Accept `'YYYY-MM-DD'` strings or `date`/`datetime` objects.
3. Fetch via existing `self._get(...)` so it inherits verify/session/timeout.
4. Refactor `parse_news_rows` to read `symbol` from each block's own
   "Trading Code" cell rather than the passed-in argument; both `get_news_df`
   and `get_all_news_df` share the parser.
5. Post-process identically to `get_news_df`: `pd.to_datetime(errors='coerce')`,
   drop NaT, sort newest-first, convert `date` back to `.date`. No `years` cutoff.
6. Return an empty DataFrame (same columns) when there are no records.
7. Do not filter pseudo/non-issuer codes inside the library — return everything.

## Non-Functional Requirements
- Performance: one HTTP request for the whole market; a 1-year window pulls ~17k
  blocks in ~20s. Caller controls timeout via the constructor.
- Backward compatibility: `get_news_df` signature and behavior unchanged.
- Security: no new secrets; same DSE endpoint and session handling.

## Acceptance Criteria
- [ ] `get_all_news_df` exists with the documented signature and docstring.
- [ ] `parse_news_rows` reads symbol from the page's Trading Code cell.
- [ ] `get_news_df` still returns the same columns/ordering/cutoff behavior.
- [ ] A unit test (mocked HTML fixture) asserts multiple distinct symbols are
      parsed from one page and grouped correctly.
- [ ] No empty `symbol`/`date`/`title` in parsed multi-symbol output.
- [ ] Package version bumped for release.

## Out of Scope
- Filtering pseudo-codes / market-wide announcement rows (consumer's decision).
- A `save_all_news_data` helper (not requested).
- Rewriting MarketWiki BD's `sync_news` (downstream, post-release).

## Notes
- `parse_news_rows`'s `symbol` argument becomes a fallback/default only; the page
  value wins when present. Document that market-wide announcements appear under
  non-issuer codes (e.g. `EXCH`).
