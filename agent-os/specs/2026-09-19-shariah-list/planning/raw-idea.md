# Raw Idea: Shariah List

**Type:** feature
**Slug:** shariah-list
**Created:** 2026-09-19

## Original Input

```
shariah-list: ShariahData scraper for Shariah-compliant company lists with a
pluggable source registry (CSE CSI implemented first; DSE DSES documented as
paid/unavailable)
```

User instruction preceding the command:

```
okay, implement CSI list scraping for getting Shariah compliant list, the source
would be CSE, and add scope for other sources as well. Create a generic method
and use paramet to define sources so that we can add more sources later. Add
comments in the method for all sources and other info like date when the list
was updated etc

start with /feature-new
```

Context established in the same conversation (verified live on 2026-09-19):

- DSE publishes the DSES index *value* but not its constituent list. The
  Financial Express (2023-03-12) reports DSE sells the DSES constituent data
  (Tk 0.5 million one-off + Tk 0.12 million/year); the only DSES document on
  dsebd.org is a 2014 image-only methodology brochure (`assets/pdf/DSES.pdf`).
- Third-party DSES component pages are partial or empty (TradingView shows 10
  rows without login; Investing.com renders "No results found"; AmarStock shows
  the index quote only).
- CSE publishes the CSE Shariah Index (CSI) constituents free:
  - `https://www.cse.com.bd/market/sectorindexdata` -> table titled
    "CSI Share by Company Name on <Month DD, YYYY>" with 103 stock codes.
  - `https://www.cse.com.bd/media/press_release` -> semi-annual "CSE Shariah
    Index revised" releases (latest #332, dated May 19, 2026, effective
    03 June 2026) naming every constituent plus additions and exclusions.

## Parsed Values

- **Slug:** shariah-list
- **Title:** Shariah List
- **Notes:** Generic, source-parameterised method. CSE (CSI) is the first and
  only implemented source; the registry must make adding DSE or third-party
  sources a data change plus one parser. Each source entry documents its URLs,
  provider, screening methodology, review cycle and access status. Output
  carries the date the list was last updated (revision and effective dates)
  and the as-of trading date of the constituent table.
