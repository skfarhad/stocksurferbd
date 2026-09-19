#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Scraper for Shariah-compliant company lists, by source.

Bangladesh has two Shariah equity indices, but only one exchange publishes the
companies behind its index (all facts below verified live on 2026-09-19):

* **CSE -- CSE Shariah Index (CSI)**: free. The constituents are printed on
  ``https://www.cse.com.bd/market/sectorindexdata`` as a table titled
  ``"CSI Share by Company Name on <Month DD, YYYY>"``, and every semi-annual
  revision is announced in a "CSE Shariah Index revised" press release at
  ``https://www.cse.com.bd/media/press_release`` that names the additions,
  exclusions and the full selected list. **This is the implemented source.**
* **DSE -- DSEX Shariah Index (DSES)**: value only. DSE sells the constituent
  list to market operators (The Financial Express, 2023-03-12: Tk 0.5 million
  one-off plus Tk 0.12 million per year) and the only public DSES document is a
  2014 image-only methodology brochure (``dsebd.org/assets/pdf/DSES.pdf``).
  Third-party component pages are login-gated (TradingView, 10 rows free),
  empty (Investing.com) or quote-only (AmarStock). **Registered, not available.**

Sources are data, not code: :attr:`ShariahData.SOURCES` describes each one
(URLs, provider, screening, review cycle, access) and names the fetcher method
that implements it. Adding a source means one registry entry plus one fetcher
returning the common ``{"as_of_date", "codes", "revision"}`` dict; the public
methods do not change.

Three different dates travel with the data, so they are named explicitly:

* ``AS_OF_DATE`` -- the *trading date* printed in the constituent table title.
  It moves every trading day and says nothing about when the list changed.
* ``LIST_REVISED_DATE`` -- the date the exchange *announced* the revision
  (the "Dhaka, May 19, 2026:" dateline of the press release).
* ``LIST_EFFECTIVE_DATE`` -- the date the revised list *took effect* in the
  index ("effective from 03 June 2026").
"""

import os
import re
import html as html_lib

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser

from .utils import HttpScraper, StockSurferError, FetchError, ParseError


class ShariahData(HttpScraper):
    # ------------------------------------------------------------------ #
    # Source registry
    # ------------------------------------------------------------------ #
    # One entry per source. Field meanings:
    #   market        exchange the codes belong to ("CSE" / "DSE")
    #   index         Shariah index whose constituents are returned
    #   list_url      page carrying the standing constituent list (GET)
    #   revision_url  page announcing revisions; supplies the two list dates
    #   provider      who maintains the index / screening
    #   screening     how compliance is decided
    #   review_cycle  how often the list is re-screened
    #   access        "free" or "paid" (public availability of the *list*)
    #   notes         provenance and caveats, shown to users in errors/info
    #   fetcher       name of the ShariahData method that returns the common
    #                 {"as_of_date", "codes", "revision"} dict, or None when the
    #                 source is documented but cannot be scraped
    SOURCES = {
        "CSE": {
            "market": "CSE",
            "index": "CSI",
            # Constituent table "CSI Share by Company Name on <date>". The same
            # page repeats id="dataTablex" for CSE30/CSE50/CSCX/CASPI and a
            # sector table, so the CSI table is located by its title text.
            "list_url": "https://www.cse.com.bd/market/sectorindexdata",
            # Newest-first listing; the latest "CSE Shariah Index revised"
            # item links to /media/press_release/<id> with the dateline,
            # effective date, added/excluded names and the full selected list.
            "revision_url": "https://www.cse.com.bd/media/press_release",
            "provider": "Chittagong Stock Exchange PLC",
            "screening": (
                "CSE's own screen over all CSE-listed companies excluding "
                "mutual funds and corporate bonds; non-compliant or delisted "
                "constituents are removed compulsorily."
            ),
            "review_cycle": (
                "Semi-annual; data for the six months ending June and "
                "December. Revisions announced in May/June and Nov/Dec."
            ),
            "access": "free",
            "notes": (
                "Free standing list. Nearly all DSE stocks are dual-listed on "
                "CSE, so CSI is a close but not identical proxy for DSES: the "
                "screening methodology differs (e.g. GRAMEENPHONE was dropped "
                "from CSI in the June 2026 revision while it remains a DSES "
                "constituent on third-party sites)."
            ),
            "fetcher": "_fetch_cse",
        },
        "DSE": {
            "market": "DSE",
            "index": "DSES",
            # DSE publishes only the index value (home page / day-wise table,
            # see IndexData). There is no constituent page to scrape.
            "list_url": None,
            "revision_url": None,
            "provider": "Dhaka Stock Exchange PLC with S&P Dow Jones Indices",
            "screening": (
                "S&P Shariah methodology; S&P DJI (via Rating Intelligence) "
                "supplies DSE the passing securities at each rebalancing."
            ),
            "review_cycle": "Periodic S&P rebalancing (monthly screens).",
            "access": "paid",
            "notes": (
                "DSE sells the DSES constituent list (The Financial Express, "
                "2023-03-12: Tk 0.5 million one-off plus Tk 0.12 million per "
                "year). The only public document is the 2014 image-only "
                "methodology PDF at dsebd.org/assets/pdf/DSES.pdf. Third-party "
                "component pages are login-gated or empty. Use source='CSE'."
            ),
            "fetcher": None,
        },
    }

    # ------------------------------------------------------------------ #
    # Output schemas
    # ------------------------------------------------------------------ #
    LIST_COLUMNS = [
        "SOURCE", "INDEX", "TRADING_CODE",
        "AS_OF_DATE", "LIST_REVISED_DATE", "LIST_EFFECTIVE_DATE",
    ]
    REVISION_COLUMNS = [
        "SOURCE", "INDEX", "LIST_REVISED_DATE", "LIST_EFFECTIVE_DATE",
        "CHANGE", "COMPANY_NAME",
    ]
    SOURCES_COLUMNS = [
        "SOURCE", "MARKET", "INDEX", "AVAILABLE", "PROVIDER", "REVIEW_CYCLE",
        "ACCESS", "LIST_URL", "REVISION_URL", "NOTES",
    ]
    CHANGE_ADDED = "ADDED"          # entered the index in the latest revision
    CHANGE_EXCLUDED = "EXCLUDED"    # dropped in the latest revision
    CHANGE_SELECTED = "SELECTED"    # full post-revision list as named in the release

    # ---- CSE page anatomy ---------------------------------------------- #
    # Title cell of the constituent table, followed by " on <Month DD, YYYY>".
    CONSTITUENT_TITLE_CSE = "{index} Share by Company Name"
    # Text that identifies a Shariah revision item in the press-release list.
    REVISION_TITLE_KEYWORD_CSE = "Shariah Index revised"

    # Wording of the "CSE Shariah Index revised" releases, checked against the
    # releases of 2024-05-12 (#250), 2024-11-13 (#273), 2025-05-27 (#292),
    # 2025-12-07 (#315) and 2026-05-19 (#332). Observed variants:
    #   dateline    "Dhaka, May 19, 2026:" / "Dhaka, December 07, 2025:"
    #   effective   "effective from 03 June 2026." / "18 December, 2025." /
    #               "June 03, 2025." / "November 25, 2024."
    #   added       "The new 3 companies which has been included are A, B and C."
    #               "The new 1 company which has been included is A."
    #               "The new 06 companies which have been included are ..."
    #               "No new company has been included in CSE Shariah Index (CSI)."
    #   excluded    "N companies i.e., A, B and C were excluded from the previous list."
    #               (sometimes "..., and C," with an Oxford comma / trailing comma)
    #   selected    "In the revised CSE Shariah Index, 103 listed companies out of
    #                383 listed Companies have been selected. These are- A, B, ..."
    #               ("These are-aamra ..." without a space in older releases)
    _RE_REVISED = re.compile(r"Dhaka,\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})\s*:", re.I)
    _RE_EFFECTIVE = re.compile(
        r"effective\s+from\s+"
        r"(\d{1,2}\s+[A-Za-z]+,?\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        re.I,
    )
    _RE_ADDED = re.compile(
        r"been\s+included\s+(?:is|are)\s+(.+?)\.?\s+On\s+the\s+other\s+hand", re.I | re.S
    )
    _RE_NO_ADDED = re.compile(r"No\s+new\s+compan(?:y|ies)\s+(?:has|have)\s+been\s+included", re.I)
    _RE_EXCLUDED = re.compile(r"i\.e\.,?\s*(.+?),?\s+were\s+excluded", re.I | re.S)
    _RE_SELECTED = re.compile(
        r"(\d+)\s+listed\s+companies\s+out\s+of\s+(\d+)\s+listed\s+companies\s+"
        r"have\s+been\s+selected\.?\s*These\s+are[-–:\s]*(.+)$",
        re.I | re.S,
    )
    # The selected list runs to the end of the release, followed by a contact
    # footer whose lead-in varies: "For detail please contact: Tania Begum
    # Asst. Manager ..." (#250-#332) or just "Tania Begum Assistant Manager
    # Chittagong Stock Exchange PLC Mobile: ..." (#315). Cut at the first
    # footer marker, then drop a leftover person name after the sentence end.
    _RE_FOOTER = re.compile(
        r"\s+(?:For\s+detail|Mobile\s*:|(?:Asst\.?|Assistant)\s+Manager|"
        r"(?:AM|SO)-P|Exchange\s+Branding)",
        re.I,
    )
    # Words that mark a trailing fragment as a company, not a person's name.
    _RE_COMPANY_WORD = re.compile(
        r"\b(?:LIMITED|LTD|PLC|COMPANY|CO|CORPORATION|BANK|INSURANCE|MILLS|"
        r"INDUSTRIES|FUND|POWER|PHARMA\w*|TEXTILES?|CERAMICS?|FOODS?)\b",
        re.I,
    )

    # ------------------------------------------------------------------ #
    # Source validation and discovery
    # ------------------------------------------------------------------ #
    @classmethod
    def _check_source(cls, source):
        """Resolve ``source`` to ``(name, entry)`` or raise.

        Unknown names raise ``ValueError`` listing the registry; known but
        unavailable sources (no fetcher) raise ``IOError`` quoting why.
        """
        name = str(source).strip().upper()
        if name not in cls.SOURCES:
            raise ValueError(
                f"Unknown Shariah list source {source!r}; choose from "
                f"{', '.join(cls.SOURCES)}."
            )
        entry = cls.SOURCES[name]
        if entry["fetcher"] is None:
            raise IOError(
                f"The {name} Shariah list ({entry['index']}) is not publicly "
                f"available ({entry['access']}). {entry['notes']}"
            )
        return name, entry

    @classmethod
    def list_sources(cls):
        """All registered sources, one row each, with ``AVAILABLE`` flag."""
        rows = []
        for name, entry in cls.SOURCES.items():
            rows.append({
                "SOURCE": name,
                "MARKET": entry["market"],
                "INDEX": entry["index"],
                "AVAILABLE": entry["fetcher"] is not None,
                "PROVIDER": entry["provider"],
                "REVIEW_CYCLE": entry["review_cycle"],
                "ACCESS": entry["access"],
                "LIST_URL": entry["list_url"],
                "REVISION_URL": entry["revision_url"],
                "NOTES": entry["notes"],
            })
        return pd.DataFrame(rows, columns=cls.SOURCES_COLUMNS)

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #
    def _get_text(self, url):
        """GET ``url`` and return its body, wrapping network errors in FetchError."""
        try:
            resp = self._get(url)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise FetchError(f"Failed to fetch {url}: {e}") from e
        return resp.text

    @staticmethod
    def _clean_text(node_or_html):
        """Collapse whitespace and unescape entities in a soup node's text."""
        text = node_or_html.get_text(" ") if hasattr(node_or_html, "get_text") else node_or_html
        return " ".join(html_lib.unescape(text).split())

    @staticmethod
    def _parse_date(text):
        """Parse a release date string to ``date``; ``None`` when absent/invalid."""
        if not text:
            return None
        try:
            return parser.parse(text.replace(",", " ")).date()
        except (ValueError, OverflowError):
            return None

    @staticmethod
    def _split_names(text):
        """Split a prose list "A, B, C and D" into names.

        Company names may themselves contain "and" ("... GENERATIONS AND
        SYSTEMS LIMITED"), so only the final comma-separated piece is split,
        and only at its first "and". Every name is normalised by stripping
        surrounding whitespace and trailing "." / "," so that "LTD." and "LTD"
        compare equal regardless of whether it ended a sentence.
        """
        if not text:
            return []
        pieces = [p.strip() for p in text.split(",")]
        pieces = [p for p in pieces if p]
        if pieces:
            last = re.split(r"\s+and\s+", pieces[-1], maxsplit=1, flags=re.I)
            if len(last) == 2:
                pieces[-1:] = last
            elif re.match(r"^and\s+", pieces[-1], re.I):      # ", and D"
                pieces[-1] = re.sub(r"^and\s+", "", pieces[-1], flags=re.I)
        return [p.strip().rstrip(".,").strip() for p in pieces if p.strip(" .,")]

    @classmethod
    def _strip_footer(cls, text):
        """Remove the contact footer that follows the selected-companies list.

        Cuts at the first :attr:`_RE_FOOTER` marker. If what remains still
        ends in "<sentence>. <Some Name>" and that trailing fragment has no
        company word in it (e.g. "Tania Begum"), the fragment is dropped too.
        The check protects names with an inner ". " such as "Kohinoor Chemical
        Co. (BD) Ltd." from being truncated.
        """
        m = cls._RE_FOOTER.search(text)
        if m:
            text = text[:m.start()]
        head, sep, tail = text.rpartition(". ")
        if sep and tail and not cls._RE_COMPANY_WORD.search(tail) and "," not in tail:
            text = head + "."
        return text.strip()

    # ------------------------------------------------------------------ #
    # CSE parsers (pure; tested against saved fixtures)
    # ------------------------------------------------------------------ #
    @classmethod
    def parse_constituents_cse(cls, html, index="CSI"):
        """Parse the "<index> Share by Company Name on <date>" table.

        Returns ``(as_of_date, codes)`` where ``as_of_date`` is the trading
        date in the title and ``codes`` the STOCK CODE column in page order.
        The page repeats ``id="dataTablex"`` for several indices, so the table
        is chosen by title text. Raises ``ParseError`` when absent.
        """
        title_prefix = cls.CONSTITUENT_TITLE_CSE.format(index=index.upper())
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            first_cell = table.find("th")
            if first_cell is None:
                continue
            title = cls._clean_text(first_cell)
            if not title.startswith(title_prefix):
                continue
            as_of = cls._parse_date(title.partition(" on ")[2])
            if as_of is None:
                raise ParseError(
                    f"CSE {index} table found but its title has no date: {title!r}"
                )
            codes = []
            body = table.find("tbody") or table
            for row in body.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue                      # header / separator rows
                code = cls._clean_text(cells[1]).upper()
                if code:
                    codes.append(code)
            if not codes:
                raise ParseError(f"CSE {index} constituent table has no rows.")
            return as_of, codes
        raise ParseError(
            f"Could not locate the '{title_prefix}' table on the CSE indices "
            "page; the page layout may have changed."
        )

    @classmethod
    def find_latest_revision_url_cse(cls, html):
        """URL of the newest "CSE Shariah Index revised" release, or ``None``.

        The listing is newest first; the first ``div.media_list_title`` link
        whose text contains :attr:`REVISION_TITLE_KEYWORD_CSE` wins.
        """
        soup = BeautifulSoup(html, "html.parser")
        keyword = cls.REVISION_TITLE_KEYWORD_CSE.lower()
        for title in soup.select("div.media_list_title"):
            link = title.find("a", href=True)
            if link is not None and keyword in cls._clean_text(link).lower():
                return link["href"]
        return None

    @classmethod
    def parse_revision_cse(cls, html):
        """Parse one "CSE Shariah Index revised" release into a dict.

        Keys: ``revised_date`` (dateline), ``effective_date``, ``added``,
        ``excluded``, ``selected`` (lists of company names as written),
        ``selected_count`` and ``total_listed`` (the "N out of M" figures).
        Any part the wording does not match is ``None`` / ``[]``; only a page
        without the release body at all raises ``ParseError``.
        """
        soup = BeautifulSoup(html, "html.parser")
        block = soup.find("div", class_="media_list_short_details")
        if block is None:
            raise ParseError(
                "CSE press release body (div.media_list_short_details) not "
                "found; the page layout may have changed."
            )
        text = cls._clean_text(block)

        revised = cls._RE_REVISED.search(text)
        effective = cls._RE_EFFECTIVE.search(text)

        if cls._RE_NO_ADDED.search(text):
            added = []
        else:
            m = cls._RE_ADDED.search(text)
            added = cls._split_names(m.group(1)) if m else []

        m = cls._RE_EXCLUDED.search(text)
        excluded = cls._split_names(m.group(1)) if m else []

        m = cls._RE_SELECTED.search(text)
        selected = cls._split_names(cls._strip_footer(m.group(3))) if m else []

        return {
            "revised_date": cls._parse_date(revised.group(1)) if revised else None,
            "effective_date": cls._parse_date(effective.group(1)) if effective else None,
            "added": added,
            "excluded": excluded,
            "selected": selected,
            "selected_count": int(m.group(1)) if m else None,
            "total_listed": int(m.group(2)) if m else None,
        }

    # ------------------------------------------------------------------ #
    # Fetchers: one per available source, all returning the common dict
    # ------------------------------------------------------------------ #
    def _fetch_cse(self):
        """CSE: constituent table (required) plus latest revision (best effort).

        The list itself comes from ``list_url``. The revision dates come from
        following ``revision_url`` to the newest Shariah release; if that
        fails for any library reason the list is still returned and
        ``revision`` is ``None``, so callers always get the codes.
        """
        entry = self.SOURCES["CSE"]
        as_of_date, codes = self.parse_constituents_cse(
            self._get_text(entry["list_url"]), entry["index"]
        )
        revision = None
        try:
            listing = self._get_text(entry["revision_url"])
            url = self.find_latest_revision_url_cse(listing)
            if url is None:
                raise ParseError(
                    f"No '{self.REVISION_TITLE_KEYWORD_CSE}' item found on "
                    f"{entry['revision_url']}."
                )
            revision = self.parse_revision_cse(self._get_text(url))
            revision["url"] = url
        except StockSurferError as e:
            print(f"Warning: CSE Shariah revision details unavailable: {e}")
        return {"as_of_date": as_of_date, "codes": codes, "revision": revision}

    def _load(self, source):
        """Validate ``source`` and run its fetcher -> ``(name, entry, data)``."""
        name, entry = self._check_source(source)
        data = getattr(self, entry["fetcher"])()
        return name, entry, data

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_shariah_list_df(self, source="CSE"):
        """Current Shariah-compliant trading codes from ``source``.

        Columns: ``SOURCE, INDEX, TRADING_CODE, AS_OF_DATE, LIST_REVISED_DATE,
        LIST_EFFECTIVE_DATE``. ``AS_OF_DATE`` is the trading date of the
        constituent table; the two list dates come from the latest revision
        announcement and are ``None`` when it could not be read.
        """
        name, entry, data = self._load(source)
        revision = data["revision"] or {}
        rows = [{
            "SOURCE": name,
            "INDEX": entry["index"],
            "TRADING_CODE": code,
            "AS_OF_DATE": data["as_of_date"],
            "LIST_REVISED_DATE": revision.get("revised_date"),
            "LIST_EFFECTIVE_DATE": revision.get("effective_date"),
        } for code in data["codes"]]
        return pd.DataFrame(rows, columns=self.LIST_COLUMNS)

    def get_shariah_revision_df(self, source="CSE"):
        """Latest revision of the ``source`` list, one row per company.

        ``CHANGE`` is ``ADDED`` / ``EXCLUDED`` / ``SELECTED`` (the full
        post-revision list as named in the announcement) and ``COMPANY_NAME``
        is the name as written there (not a trading code). Empty when the
        announcement could not be read.
        """
        name, entry, data = self._load(source)
        revision = data["revision"]
        rows = []
        if revision:
            groups = (
                (self.CHANGE_ADDED, revision["added"]),
                (self.CHANGE_EXCLUDED, revision["excluded"]),
                (self.CHANGE_SELECTED, revision["selected"]),
            )
            for change, names in groups:
                for company in names:
                    rows.append({
                        "SOURCE": name,
                        "INDEX": entry["index"],
                        "LIST_REVISED_DATE": revision["revised_date"],
                        "LIST_EFFECTIVE_DATE": revision["effective_date"],
                        "CHANGE": change,
                        "COMPANY_NAME": company,
                    })
        return pd.DataFrame(rows, columns=self.REVISION_COLUMNS)

    def get_shariah_list_info(self, source="CSE"):
        """Metadata dict: registry fields plus counts, dates and change lists."""
        name, entry, data = self._load(source)
        revision = data["revision"] or {}
        info = {"source": name}
        info.update({k: v for k, v in entry.items() if k != "fetcher"})
        info.update({
            "as_of_date": data["as_of_date"],
            "constituent_count": len(data["codes"]),
            "list_revised_date": revision.get("revised_date"),
            "list_effective_date": revision.get("effective_date"),
            "selected_count": revision.get("selected_count"),
            "total_listed": revision.get("total_listed"),
            "added": list(revision.get("added", [])),
            "excluded": list(revision.get("excluded", [])),
            "revision_announcement_url": revision.get("url"),
        })
        return info

    def save_shariah_list(self, file_path="", file_name="shariah_list.xlsx", source="CSE"):
        self.get_shariah_list_df(source=source).to_excel(
            os.path.join(file_path, file_name), index=False
        )
        print("Shariah list download completed!")

    def save_shariah_revision(self, file_path="", file_name="shariah_revision.xlsx",
                              source="CSE"):
        self.get_shariah_revision_df(source=source).to_excel(
            os.path.join(file_path, file_name), index=False
        )
        print("Shariah revision download completed!")
