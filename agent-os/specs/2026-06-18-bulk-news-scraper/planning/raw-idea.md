# Raw Idea: Bulk date-range news scraper

**Type:** feature
**Slug:** bulk-news-scraper
**Created:** 2026-06-18

## Original Input

```
Add a bulk, date-range news scraper to FundamentalData (one call for all symbols)

Today FundamentalData.get_news_df(symbol, years=2) fetches news per symbol — it hits NEWS_URL + symbol (https://www.dsebd.org/old_news.php?archive=news&criteria=3&inst=<symbol>), one HTTP request per company. A consumer that wants the whole market makes ~400 requests, which is slow and failure-prone.

DSE's old_news.php also supports a date-range mode that returns every symbol's news in a single request. I verified this against the live site:

URL: https://www.dsebd.org/old_news.php?archive=news&criteria=4&startDate=<YYYY-MM-DD>&endDate=<YYYY-MM-DD>&inst=
criteria=4 = filter by date range; startDate/endDate are required; inst left empty = all symbols.
A 1-year window returned 17,446 news blocks across 802 trading codes in ~21s, with 0 missing fields.
A 3-day window returned ~98 codes / ~214 items in well under a second.
The response is the same table.table-news structure parse_news_rows already parses, and each news block contains its own Trading Code cell, so the symbol can be read straight from the page rather than passed in.

Task: add a new method (keep get_news_df unchanged for backward compatibility):

def get_all_news_df(self, start_date, end_date):
    """
    All companies' news/disclosures over a date range in a SINGLE request.

    Hits old_news.php in date-range mode (criteria=4, empty inst), so one call
    returns every symbol's news instead of one request per symbol.

    Args:
        start_date, end_date: 'YYYY-MM-DD' strings (or date objects).
    Returns:
        DataFrame [symbol, date, title, news], newest first. The `symbol`
        comes from each block's own 'Trading Code' cell. Empty DataFrame if none.
    """

Implementation notes:
- Build the URL with criteria=4, startDate, endDate, empty inst; fetch via the existing self._get(...) (so it inherits verify/session/timeout from HttpScraper).
- Refactor parse_news_rows so the symbol is taken from the page's Trading Code cell, not the symbol argument. The current loop already starts a new record on the "Trading Code" label — set current['symbol'] = value there. Then get_news_df (single symbol) and get_all_news_df (bulk) can share the same parser. (Single-symbol pages also carry the Trading Code cell, so this is safe.)
- Apply the same post-processing as get_news_df: pd.to_datetime(errors='coerce'), drop NaT, sort newest-first, convert back to .date. No years cutoff needed — the date range already bounds it.
- Use a reasonable timeout (a 1-year pull takes ~20s); the caller can pass timeout= to the constructor.
- Do not filter pseudo-codes (e.g. EXCH "DSE NEWS: Daily Turnover…") inside the library — return everything and let the consumer decide. Just document that market-wide announcements appear under non-issuer codes.

Validation:
- Add a test (mock the HTML fixture) asserting multiple distinct symbols are parsed from one page and grouped correctly.
- Manual smoke check: FundamentalData(verify=False).get_all_news_df('2026-06-15','2026-06-17') should return a multi-symbol DataFrame with no empty symbol/date/title.

After release, bump the version so the MarketWiki BD project can pin it and rewrite its sync_news to make one range call per run instead of ~400.
```

## Parsed Values

- **Slug:** bulk-news-scraper
- **Title:** Bulk date-range news scraper
- **Notes:** Keep `get_news_df` unchanged for backward compatibility. Refactor `parse_news_rows` to read symbol from the page. Bump package version after release.
