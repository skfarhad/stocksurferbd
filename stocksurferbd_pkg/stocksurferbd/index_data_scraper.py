#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Scraper for DSE market indices (DSEX, DSES, DS30, DGEN, CDSET).

Unlike :class:`PriceData`, which targets per-company share tables, this loader
reads the aggregate *index* values published by DSE. DSE serves the indices in a
few different ways, so there are dedicated methods:

* ``get_index_history_df`` / ``save_index_history`` -- the day-wise table on
  ``recent_market_information.php`` (rolling ~30 days) or, when a date range is
  given, ``recent_market_information_more.php`` (full archive, ~2010 onward).
  Covers ``DSEX``, ``DSES``, ``DS30`` and ``DGEN`` (availability varies by each
  index's launch date). No CDSET column.
* ``get_index_graph_df`` / ``save_index_graph`` -- the per-index daily close
  series behind the home-page graph, by month-count. Serves ``CDSET`` (back to
  ~2016) and ``DS30``. This is the only source of historical CDSET values.
* ``get_current_indices_df`` / ``save_current_indices`` -- the live "Indices"
  box on the home page. Covers ``DSEX``, ``DSES``, ``DS30`` **and** ``CDSET``.
* ``get_intraday_df`` / ``save_intraday`` -- the per-minute series behind the
  home-page graph, for any single index including ``CDSET`` (current day only).
"""

import os
import re
import datetime

import pandas as pd
from dateutil import parser
from bs4 import BeautifulSoup

from .utils import HttpScraper, parse_float, parse_int


class IndexData(HttpScraper):
    # Rolling ~30-day table (no date range).
    INDEX_HISTORY_URL_DSE = "https://www.dsebd.org/recent_market_information.php"
    # Same table, but accepts a startDate/endDate POST -> full archive (2010+).
    INDEX_ARCHIVE_URL_DSE = "https://www.dsebd.org/recent_market_information_more.php"
    HOME_URL_DSE = "https://www.dsebd.org/"
    # Per-index daily close series by month-count (the only history for CDSET).
    GRAPH_URL_DSE = "https://www.dsebd.org/php_graph/monthly_graph_index.php"

    SUPPORTED_INDICES = ("DSEX", "DSES", "DS30", "CDSET")

    # Indices the graph endpoint serves, mapped to its 'type' query value.
    # CDSET is only available here (it has no column in the day-wise archive).
    _GRAPH_TYPES = {"CDSET": "cdset", "DS30": "ds30"}

    # Index name -> the JavaScript variable holding its intraday tick series on
    # the home page. DSEX is published under the legacy "dsbi" name.
    _INTRADAY_JS_VAR = {
        "DSEX": "index_value_dsbi",
        "DSES": "index_value_dses",
        "DS30": "index_value_ds30",
        "CDSET": "index_value_cdset",
    }

    # Column order of the day-wise table as published by DSE.
    _HISTORY_COLUMNS = (
        "DATE", "TOTAL_TRADE", "TOTAL_VOLUME", "VALUE_MN",
        "MARKET_CAP_MN", "DSEX", "DSES", "DS30", "DGEN",
    )

    @staticmethod
    def _num(str_val):
        """Parse a numeric cell, treating '-'/'--'/'' as missing (None)."""
        cleaned = str_val.strip().rstrip("%").strip()
        if cleaned in ("", "-", "--"):
            return None
        return parse_float(cleaned)

    @staticmethod
    def save_excel(dict_list, file_path):
        pd.DataFrame(dict_list).to_excel(file_path)

    # ------------------------------------------------------------------ #
    # Day-wise history (DSEX / DSES / DS30 / DGEN)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _find_history_table(soup):
        """Return the day-wise table (header has 'Date' and a 'DSEX' column).

        The page has two same-class tables -- an all-time 'record high' table
        and the day-wise series -- so we select by header content, not class.
        """
        for table in soup.find_all("table"):
            first_row = table.find("tr")
            if first_row is None:
                continue
            headers = [" ".join(c.get_text().split())
                       for c in first_row.find_all(["th", "td"])]
            if "Date" in headers and any("DSEX" in h for h in headers):
                return table
        return None

    @staticmethod
    def _fmt_date(value):
        """Normalise a date input to the ``YYYY-MM-DD`` the form expects."""
        if value is None:
            return None
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime("%Y-%m-%d")
        return parser.parse(str(value)).strftime("%Y-%m-%d")

    @classmethod
    def parse_index_history(cls, soup):
        """Parse the day-wise index table from a fetched page's soup."""
        table = cls._find_history_table(soup)
        if table is None:
            raise ValueError(
                "Could not locate the DSE index time-series table; the page "
                "layout may have changed."
            )
        dict_list = []
        for row in table.find_all("tr")[1:]:  # skip header
            cells = [" ".join(c.get_text().split()) for c in row.find_all("td")]
            if len(cells) < len(cls._HISTORY_COLUMNS):
                continue
            try:
                dict_list.append({
                    "DATE": parser.parse(cells[0], dayfirst=True).date(),
                    "TOTAL_TRADE": parse_int(cells[1]) if cells[1] not in ("", "-") else None,
                    "TOTAL_VOLUME": parse_int(cells[2]) if cells[2] not in ("", "-") else None,
                    "VALUE_MN": cls._num(cells[3]),
                    "MARKET_CAP_MN": cls._num(cells[4]),
                    "DSEX": cls._num(cells[5]),
                    "DSES": cls._num(cells[6]),
                    "DS30": cls._num(cells[7]),
                    "DGEN": cls._num(cells[8]),
                })
            except Exception as e:  # keep parsing remaining rows
                print(str(e))
        return dict_list

    def parse_index_history_dse(self, start_date=None, end_date=None):
        if start_date is None and end_date is None:
            # No range -> the rolling ~30-day table (single GET).
            page = self._get(self.INDEX_HISTORY_URL_DSE)
        else:
            # Any range -> the archive endpoint (POST). Default the missing
            # side to a sensible bound so a one-sided range still works.
            end = self._fmt_date(end_date) or datetime.date.today().strftime("%Y-%m-%d")
            start = self._fmt_date(start_date) or "2010-01-01"
            page = self._post(self.INDEX_ARCHIVE_URL_DSE, {
                "startDate": start,
                "endDate": end,
                "searchRecentMarket": "Search Recent Market",
            })
        return self.parse_index_history(BeautifulSoup(page.text, "html.parser"))

    def get_index_history_df(self, market="DSE", start_date=None, end_date=None):
        """Day-wise index values (DSEX/DSES/DS30/DGEN) as a DataFrame.

        With no dates, returns the rolling ~30-day table. Pass ``start_date``
        and/or ``end_date`` (``date``/``datetime`` or any parseable string) to
        pull the full DSE archive (data available from ~2010 onward).
        """
        if market != "DSE":
            raise IOError("Only 'DSE' is supported for index data.")
        return pd.DataFrame(
            self.parse_index_history_dse(start_date=start_date, end_date=end_date)
        )

    def save_index_history(self, file_path="", file_name="index_data.xlsx",
                           market="DSE", start_date=None, end_date=None):
        rows = self.get_index_history_df(
            market=market, start_date=start_date, end_date=end_date
        ).to_dict("records")
        self.save_excel(rows, os.path.join(file_path, file_name))

    # ------------------------------------------------------------------ #
    # Live snapshot (DSEX / DSES / DS30 / CDSET)
    # ------------------------------------------------------------------ #
    @classmethod
    def parse_current_indices(cls, html):
        """Parse the live "Indices" box from the home-page HTML text."""
        soup = BeautifulSoup(html, "html.parser")
        result = {}

        # DSEX / DSES / DS30 come from the ".midrow" widgets (the box repeats
        # the values, so keep only the first occurrence of each index).
        for mr in soup.find_all(class_="midrow"):
            name_col = mr.find(class_="m_col-1")
            if name_col is None:
                continue  # header/label row without index data
            name = "".join(name_col.get_text().split())
            name = name.replace("Index", "").upper()  # e.g. "DSEXIndex" -> "DSEX"
            if name not in cls.SUPPORTED_INDICES or name in result:
                continue
            cols = [mr.find(class_=f"m_col-{i}") for i in (2, 3, 4)]
            result[name] = {
                "INDEX": name,
                "POINTS": cls._num(cols[0].get_text()) if cols[0] else None,
                "CHANGE": cls._num(cols[1].get_text()) if cols[1] else None,
                "PCT_CHANGE": cls._num(cols[2].get_text()) if cols[2] else None,
            }

        # CDSET has no midrow; take the last tick of its intraday JS series.
        cdset_ticks = cls._parse_intraday_js(html, "CDSET")
        if cdset_ticks:
            result["CDSET"] = {
                "INDEX": "CDSET",
                "POINTS": cdset_ticks[-1][1],
                "CHANGE": None,       # not published on the home page
                "PCT_CHANGE": None,
            }

        return [result[i] for i in cls.SUPPORTED_INDICES if i in result]

    def parse_current_indices_dse(self):
        return self.parse_current_indices(self._get(self.HOME_URL_DSE).text)

    def get_current_indices_df(self, market="DSE"):
        """Live snapshot of DSEX/DSES/DS30/CDSET as a DataFrame."""
        if market != "DSE":
            raise IOError("Only 'DSE' is supported for index data.")
        return pd.DataFrame(self.parse_current_indices_dse())

    def save_current_indices(self, file_path="", file_name="current_indices.xlsx", market="DSE"):
        rows = self.get_current_indices_df(market=market).to_dict("records")
        self.save_excel(rows, os.path.join(file_path, file_name))

    # ------------------------------------------------------------------ #
    # Daily close history for CDSET / DS30 (graph endpoint, by month-count)
    # ------------------------------------------------------------------ #
    @staticmethod
    def parse_index_graph(text, index):
        """Parse the daily ``date,value`` close series from the graph HTML."""
        pairs = re.findall(r"(\d{4}-\d{2}-\d{2}),([\d.]+)", text)
        return [
            {"INDEX": index.upper(), "DATE": parser.parse(d).date(), "POINTS": float(v)}
            for d, v in pairs
        ]

    def parse_index_graph_dse(self, index, months):
        index = index.upper()
        if index not in self._GRAPH_TYPES:
            raise ValueError(
                f"Index {index!r} is not served by the graph endpoint; choose "
                f"from {tuple(self._GRAPH_TYPES)}. For DSEX/DSES use "
                "get_index_history_df(start_date=..., end_date=...)."
            )
        page = self._get(
            f"{self.GRAPH_URL_DSE}?type={self._GRAPH_TYPES[index]}&duration={int(months)}"
        )
        return self.parse_index_graph(page.text, index)

    def get_index_graph_df(self, index="CDSET", months=12, market="DSE"):
        """Daily close history for CDSET or DS30 over the last ``months``.

        This is the only source of historical CDSET values (data goes back to
        ~2016). ``months`` is a count, e.g. ``120`` for ~10 years.
        """
        if market != "DSE":
            raise IOError("Only 'DSE' is supported for index data.")
        return pd.DataFrame(self.parse_index_graph_dse(index, months))

    def save_index_graph(self, index="CDSET", months=12, file_path="",
                         file_name=None, market="DSE"):
        file_name = file_name or f"{index.upper()}_history.xlsx"
        rows = self.get_index_graph_df(
            index=index, months=months, market=market
        ).to_dict("records")
        self.save_excel(rows, os.path.join(file_path, file_name))

    # ------------------------------------------------------------------ #
    # Intraday ticks for one index (incl. CDSET), current day only
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_intraday_js(html, index):
        var = IndexData._INTRADAY_JS_VAR[index]
        m = re.search(re.escape(var) + r"\s*=\s*(.+?);", html, re.S)
        if not m:
            return []
        ticks = re.findall(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}),([\d.]+)", m.group(1))
        return [(ts, float(val)) for ts, val in ticks]

    @classmethod
    def parse_intraday(cls, html, index):
        """Parse the current-day per-minute tick series for one index."""
        index = index.upper()
        if index not in cls._INTRADAY_JS_VAR:
            raise ValueError(
                f"Unknown index {index!r}; choose from {cls.SUPPORTED_INDICES}."
            )
        return [
            {"INDEX": index, "DATETIME": ts, "POINTS": val}
            for ts, val in cls._parse_intraday_js(html, index)
        ]

    def parse_intraday_dse(self, index):
        return self.parse_intraday(self._get(self.HOME_URL_DSE).text, index)

    def get_intraday_df(self, index="DSEX", market="DSE"):
        """Current-day per-minute ticks for one index (DSEX/DSES/DS30/CDSET)."""
        if market != "DSE":
            raise IOError("Only 'DSE' is supported for index data.")
        return pd.DataFrame(self.parse_intraday_dse(index))

    def save_intraday(self, index="DSEX", file_path="", file_name=None, market="DSE"):
        file_name = file_name or f"{index.upper()}_intraday.xlsx"
        rows = self.get_intraday_df(index=index, market=market).to_dict("records")
        self.save_excel(rows, os.path.join(file_path, file_name))
