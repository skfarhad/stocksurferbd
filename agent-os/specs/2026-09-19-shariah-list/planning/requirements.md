# Feature Requirements: Shariah List

## Overview

Investors and downstream platforms need the standing list of Shariah-compliant
listed companies in Bangladesh. DSE does not publish its DSES constituents
(the list is a paid product), but CSE publishes the CSE Shariah Index (CSI)
constituents free on its website and announces every semi-annual revision in a
press release. `stocksurferbd` should expose that list through the same style
of API as its other scrapers, with a source registry so further sources
(DSE, if it ever opens the list; brokerage screens; index vendors) can be added
without changing the public method signatures.

Beneficiaries: users of the library who filter DSE/CSE symbols for Shariah
compliance, and the maintainer, who gets one place to document each source's
provenance and access status.

## User Stories

- As a library user, I want `ShariahData().get_shariah_list_df()` to return
  the current Shariah-compliant trading codes, so that I can filter my price
  and fundamentals data.
- As a library user, I want the returned frame to say when the list was last
  revised and from which date it applies, so that I can tell a stale list from
  a current one.
- As a library user, I want to see which companies were added and excluded in
  the latest revision, so that I can react to changes.
- As a maintainer, I want sources defined as data (URLs, provider, review
  cycle, access notes) with one parser each, so that a new source is a
  registry entry plus a parser, not a new public method.
- As a library user, I want a clear error when I ask for a source that is
  known but not available (DSE), so that I do not waste time looking for a
  page that does not exist.

## Functional Requirements

1. New public class `ShariahData(HttpScraper)` in
   `stocksurferbd_pkg/stocksurferbd/shariah_data_scraper.py`, exported from
   the package `__init__.py`.
2. A class-level `SOURCES` registry keyed by source name. Each entry records:
   market, index name, list URL, revision-announcement URL, provider,
   screening methodology, review cycle, access status and free-text notes, and
   the name of the parser method that implements it (or `None` when the source
   is documented but not available).
3. `SOURCES["CSE"]` is implemented (CSI). `SOURCES["DSE"]` is registered with
   no parser and a note explaining that DSE sells the DSES constituent list,
   so requesting it raises a clear error naming the CSE alternative.
4. Every public method takes `source="CSE"`. Source names are validated
   case-insensitively against `SOURCES`; an unknown source raises `ValueError`
   listing the valid names.
5. `get_shariah_list_df(source)` returns one row per constituent with columns
   `SOURCE, INDEX, TRADING_CODE, AS_OF_DATE, LIST_REVISED_DATE,
   LIST_EFFECTIVE_DATE`. `AS_OF_DATE` is the trading date printed in the CSE
   table title. The two list dates come from the latest revision press release
   and are `None` when the release cannot be found or parsed, without failing
   the list itself.
6. `get_shariah_revision_df(source)` returns the latest revision as one row per
   company with columns `SOURCE, INDEX, LIST_REVISED_DATE, LIST_EFFECTIVE_DATE,
   CHANGE, COMPANY_NAME` where `CHANGE` is `ADDED`, `EXCLUDED` or `SELECTED`
   (the full post-revision list as named in the release).
7. `get_shariah_list_info(source)` returns a dict of metadata: source
   description fields from the registry plus `as_of_date`, `constituent_count`,
   `list_revised_date`, `list_effective_date`, `total_listed`, `added`,
   `excluded` and the URL of the press release used.
8. `save_shariah_list` and `save_shariah_revision` write the frames to xlsx,
   following the existing `save_*` conventions (`file_path`, `file_name`).
9. `list_sources()` returns a DataFrame describing the registry so users can
   discover sources and their access status programmatically.
10. Parsers are classmethods that accept HTML text and are unit-tested against
    saved fixtures. The CSI table is selected by its title text, not by
    position or CSS id (the page repeats `id="dataTablex"` for CSCX, CASPI, CSI
    and sector tables).
11. The press-release parser tolerates the wording variations seen in releases
    #250, #273, #292, #315 and #332: "The new N company/companies which has/have
    been included is/are ...", "No new company has been included ...",
    "N companies i.e., ... were excluded ...", "N listed companies out of M
    listed Companies have been selected. These are- ...". Date strings may be
    "May 19, 2026", "December 07, 2025", "03 June 2026" or "18 December, 2025".
12. Fetch failures raise `FetchError`; a page without the expected table or
    heading raises `ParseError` naming the source.

## Non-Functional Requirements

- Performance: two GETs for the list (constituent page plus press-release
  listing) and one more for the release body. No POST or CSRF needed.
- Security: public pages only, no credentials. Honour the `verify`, `session`
  and `timeout` options of `HttpScraper`.
- Compatibility: no change to any existing class, method or output schema.
- Documentation: README usage block and output-schema rows; CHANGELOG entry;
  version bump to 2.1.0; roadmap updated.

## Acceptance Criteria

- [ ] `ShariahData().get_shariah_list_df()` against the saved CSE fixture
      returns 103 rows with `AS_OF_DATE == date(2026, 9, 19)`, `INDEX == "CSI"`,
      `SOURCE == "CSE"`, first code `AAMRANET`, last code `ZAHEENSPIN`.
- [ ] Revision parsing of release #332 yields revised date 2026-05-19,
      effective date 2026-06-03, 3 `ADDED`, 12 `EXCLUDED`, 103 `SELECTED`,
      total listed 383.
- [ ] Revision parsing of the "No new company has been included" wording
      (release #273) yields 0 `ADDED` and 3 `EXCLUDED`.
- [ ] `get_shariah_list_df(source="DSE")` raises with a message that names
      the paid status and the CSE alternative; `source="NYSE"` raises
      `ValueError` listing `CSE, DSE`.
- [ ] A press-release fetch or parse failure leaves the constituent list intact
      with the two list-date columns set to `None`.
- [ ] `list_sources()` has one row per registry entry with an `AVAILABLE`
      boolean.
- [ ] All new parsers have fixture-based tests; the existing 82 tests still
      pass.
- [ ] README, CHANGELOG, `setup.py` version and roadmap are updated.

## Out of Scope

- Mapping press-release company names to trading codes (the CSI table already
  provides codes; names are only reported in the revision frame).
- Historical reconstruction of past CSI compositions.
- Any DSES data (paid) or third-party DSES component pages (login-gated or
  empty at the time of writing). They are documented in the registry notes so
  a future source can be added.
- Shariah screening of individual companies by the library itself.

## Notes

Verified on 2026-09-19: `https://www.cse.com.bd/market/sectorindexdata`
serves the CSI table via plain GET; the press-release listing at
`https://www.cse.com.bd/media/press_release` links each "CSE Shariah Index
revised" item to `/media/press_release/<id>`. The DSE Shariah methodology PDF
is image-only (Illustrator, 2014) and contains no constituent list.
