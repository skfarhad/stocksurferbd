#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2021 The Python Packaging Authority"

import os
import re
import csv
import calendar

from bs4 import BeautifulSoup
import pandas as pd
import datetime
from dateutil import parser
import urllib.parse as parse_url

from .utils import HttpScraper, StockSurferError, ParseError, read_xlsx_bytes


class PriceData(HttpScraper):
    """Price history, day-end and live prices for DSE and CSE.

    Both markets return the **same columns, order and dtypes** (the DSE shape),
    so downstream code needs no market branch:

    * :meth:`get_price_history_df` -- one symbol over a date range
    * :meth:`get_day_end_df` -- all symbols, one day
    * :meth:`get_day_end_range_df` -- all symbols over a date range
    * :meth:`get_current_price_df` -- live snapshot of all symbols

    DSE is served per symbol by its day-end archive. CSE only publishes an
    *all-symbols-per-date-range* spreadsheet, so CSE requests are split into
    calendar chunks, downloaded once, cached on the instance (and optionally
    on disk via ``cache_dir``) and then filtered to the requested symbol.
    """

    VALID_MARKETS = ('DSE', 'CSE')

    HISTORY_URL_DSE = "https://www.dsebd.org/day_end_archive.php?endDate=<date>&archive=data"
    CURRENT_PRICE_URL_DSE = 'https://www.dsebd.org/latest_share_price_scroll_l.php'
    CKT_BREAKER_URL_DSE = 'https://www.dsebd.org/cbul.php'

    CURRENT_PRICE_URL_CSE = 'https://www.cse.com.bd/market/current_price'
    HISTORICAL_DATA_PAGE_CSE = 'https://www.cse.com.bd/market/historicaldata'
    DOWNLOAD_COMPANY_URL_CSE = 'https://www.cse.com.bd/market/data_download_company'
    COMPANY_DETAILS_URL_CSE = 'https://www.cse.com.bd/company/companydetails/'
    # A liquid symbol whose company page is read for the exchange trading date
    # when the day-end download has no rows yet.
    CSE_DATE_REFERENCE_SYMBOL = 'ACI'

    # Canonical (DSE) output schemas. CSE frames are built with these exact
    # column lists so the order is enforced rather than incidental.
    HISTORY_COLUMNS = [
        'DATE', 'TRADING_CODE', 'LTP', 'HIGH', 'LOW', 'OPENP', 'CLOSEP',
        'YCP', 'TRADE', 'VALUE_MN', 'VOLUME',
    ]
    CURRENT_COLUMNS = [
        'DATE', 'TRADING_CODE', 'LTP', 'HIGH', 'LOW', 'CLOSEP', 'YCP',
        '% CHANGE', 'TRADE', 'VALUE_MN', 'VOLUME',
    ]

    # Earliest trade_date the CSE company download serves (gaps before mid-2018).
    CSE_EARLIEST_DATE = '2015-11-24'
    CSE_CHUNK_SIZES = ('year', 'month')
    CSE_CACHE_FILE_PATTERN = 'cse_day_end_{start}_{end}.pkl'
    # CSE spreadsheet column -> canonical column.
    _CSE_HISTORY_COLUMN_MAP = {
        'trade_date': 'DATE',
        'company_code': 'TRADING_CODE',
        'last_traded_price': 'LTP',
        'day_high': 'HIGH',
        'day_low': 'LOW',
        'open_price': 'OPENP',
        'close_price': 'CLOSEP',
        'prev_close_price': 'YCP',
        'no_of_trades': 'TRADE',
        'turnover': 'VALUE_MN',
        'volume': 'VOLUME',
    }
    _CSE_DATE_LABEL_RE = re.compile(
        r'(?:Last\s+Trade|Updated)\s+Date\s*(\d{1,2}\s+[A-Za-z]+,?\s+\d{4})'
    )

    def __init__(self, verify=True, session=None, timeout=None, cache_dir=None):
        """``cache_dir`` (optional) stores closed CSE download chunks on disk
        so later instances/processes skip the network for past years."""
        super().__init__(verify=verify, session=session, timeout=timeout)
        self.cache_dir = cache_dir
        self._cse_chunk_cache = {}

    # ------------------------------------------------------------------ #
    # Small helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def get_date():
        return str(datetime.datetime.now().date())

    @staticmethod
    def _fmt_date(value):
        """Normalise a date input to the ``YYYY-MM-DD`` the form expects.

        Accepts ``None`` (-> ``None``), ``date``/``datetime`` objects, or any
        parseable string.
        """
        if value is None:
            return None
        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime("%Y-%m-%d")
        return parser.parse(str(value)).strftime("%Y-%m-%d")

    @staticmethod
    def _to_date(value):
        """Coerce a ``date``/``datetime``/parseable string to ``datetime.date``."""
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        return parser.parse(str(value)).date()

    @classmethod
    def _check_market(cls, market):
        market = str(market).strip().upper()
        if market not in cls.VALID_MARKETS:
            raise IOError('Invalid Stock Market! Possible values are- CSE, DSE')
        return market

    @staticmethod
    def _normalise_symbol(symbol):
        if symbol is None or not str(symbol).strip():
            raise ValueError("symbol must be a non-empty string")
        return str(symbol).strip().upper()

    @staticmethod
    def parse_float(str_val):
        new_val = str_val.replace(
            ',', ''
        ).replace('--', '0')
        return float(new_val)

    @staticmethod
    def parse_int(str_val):
        new_val = str_val.replace(
            ',', ''
        ).replace('--', '0')
        return int(new_val)

    @staticmethod
    def save_csv(dict_list, csv_path):
        keys = dict_list[0].keys()
        with open(csv_path, 'w+', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(dict_list)

    @staticmethod
    def save_excel(dict_list, csv_path):
        df = pd.DataFrame(dict_list)
        df.to_excel(csv_path)

    @staticmethod
    def _report_progress(progress, chunk_start, chunk_end, index, total):
        """``progress``: ``True`` prints, ``False`` is silent, a callable is
        called as ``progress(chunk_start, chunk_end, index, total)``."""
        if callable(progress):
            progress(chunk_start, chunk_end, index, total)
        elif progress:
            print(f"CSE download {chunk_start}..{chunk_end} ({index}/{total})")

    # ------------------------------------------------------------------ #
    # DSE: day-end archive (history + day-end)
    # ------------------------------------------------------------------ #
    def get_history_url(self, start_date=None, end_date=None):
        """Build the DSE day-end archive URL.

        With no arguments this returns the historical default (``endDate`` =
        today, no ``startDate``), preserving the previous behaviour. Pass
        ``start_date`` and/or ``end_date`` (``date``/``datetime`` or any
        parseable string) to bound the range; a ``startDate`` is only added to
        the query when ``start_date`` is given.
        """
        end = self._fmt_date(end_date) or self.get_date()
        url = self.HISTORY_URL_DSE.replace('<date>', end)
        start = self._fmt_date(start_date)
        if start:
            url += "&startDate=" + start
        return url

    def parse_day_end_archive(self, soup):
        """Parse the DSE day-end archive table (shared by history & day-end).

        The archive serves the same column layout whether queried for one
        ``inst`` over a date range or for ``All Instrument`` on a single day.
        Returns ``[]`` when the table is absent (e.g. an unfinished/future date
        before market close, or a non-trading day) instead of raising.
        """
        stock_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white shares-table fixedHeader"
            }
        )
        tbody = stock_table.find("tbody") if stock_table else None
        if tbody is None:
            return []
        dict_list = []
        for row in tbody.find_all("tr"):
            row_data = ["".join(td.get_text().split()) for td in row.find_all("td")]
            try:
                dict_list.append({
                    'DATE': row_data[1],
                    'TRADING_CODE': row_data[2],
                    'LTP': self.parse_float(row_data[3]),
                    'HIGH': self.parse_float(row_data[4]),
                    'LOW': self.parse_float(row_data[5]),
                    'OPENP': self.parse_float(row_data[6]),
                    'CLOSEP': self.parse_float(row_data[7]),
                    'YCP': self.parse_float(row_data[8]),
                    'TRADE': self.parse_float(row_data[9].replace(',', '')),
                    'VALUE_MN': self.parse_float(row_data[10]),
                    'VOLUME': self.parse_float(row_data[11].replace(',', '')),
                })
            except Exception as e:
                print(str(e))
        return dict_list

    def parse_price_history_dse(self, symbol, start_date=None, end_date=None):
        full_url = self.get_history_url(
            start_date=start_date, end_date=end_date
        ) + "&inst=" + parse_url.quote(symbol)
        target_page = self._get(full_url)
        return self.parse_day_end_archive(
            BeautifulSoup(target_page.text, 'html.parser')
        )

    def parse_day_end_dse(self, date=None):
        """All-instrument day-end rows for a single ``date`` (default today)."""
        day = self._fmt_date(date) or self.get_date()
        full_url = self.get_history_url(
            start_date=day, end_date=day
        ) + "&inst=" + parse_url.quote("All Instrument")
        target_page = self._get(full_url)
        return self.parse_day_end_archive(
            BeautifulSoup(target_page.text, 'html.parser')
        )

    # ------------------------------------------------------------------ #
    # DSE: live prices
    # ------------------------------------------------------------------ #
    def parse_current_prices_dse(self, soup, fp_dict=None):
        dict_list = []
        table_header = soup.find(
            'h2',
            attrs={
                'class': "BodyHead topBodyHead"
            }
        )
        # print(table_header)
        date_txt = " ".join(table_header.text.split(
            'On'
        )[1].split(
            'at'
        )[0].strip().split(

        ))
        latest_trading_date = parser.parse(date_txt).date()
        stock_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white shares-table fixedHeader"
            }
        )
        table_rows = stock_table.find_all("tr")
        # print(type(table_rows))
        for row in table_rows:
            th_values = ["".join(th.get_text().split()) for th in row.find_all("th")]
            td_values = ["".join(td.get_text().split()) for td in row.find_all("td")]
            if len(th_values):
                # print(th_values)
                continue
            # print(td_values)
            dict_list.append({
                'DATE': latest_trading_date,
                'TRADING_CODE': td_values[1],
                'LTP': self.parse_float(td_values[2]),
                'HIGH': self.parse_float(td_values[3]),
                'LOW': self.parse_float(td_values[4]),
                'CLOSEP': self.parse_float(td_values[5]),
                'YCP': self.parse_float(td_values[6]),
                '% CHANGE': self.parse_float(td_values[7]),
                'TRADE': self.parse_float(td_values[8]),
                'VALUE_MN': self.parse_float(td_values[9]),
                'VOLUME': self.parse_float(td_values[10]),
                # 'PUB_FP': fp_dict[td_values[1]][0] if fp_dict else 0,
            })
        return dict_list

    def parse_floor_prices_dse(self, soup):
        fp_price_dict = {}
        price_table = soup.find(
            "table",
            attrs={
                "class": "table table-bordered background-white text-center"
            }
        )
        table_rows = price_table.find_all("tr")
        # print(type(table_rows))
        for row in table_rows:
            th_values = ["".join(th.get_text().split()) for th in row.find_all("th")]
            td_values = ["".join(td.get_text().split()) for td in row.find_all("td")]
            if len(th_values):
                # print(th_values)
                continue
            fp_price_dict.update({
                td_values[1]: (
                    self.parse_float(td_values[5]) if td_values[5] != '-' else 0,
                    self.parse_float(td_values[8]) if td_values[8] != '-' else 0
                )
            })
        return fp_price_dict

    # ------------------------------------------------------------------ #
    # CSE: company day-end download -> canonical history frame
    # ------------------------------------------------------------------ #
    @classmethod
    def cse_download_to_history(cls, df):
        """Reshape the CSE company download into the DSE history schema.

        ``turnover`` (Taka) becomes ``VALUE_MN`` (millions, 3 dp); ``DATE``
        becomes a ``YYYY-MM-DD`` string like the DSE archive rows. Rows are
        ordered newest first, then by trading code.
        """
        missing = set(cls._CSE_HISTORY_COLUMN_MAP) - set(df.columns)
        if missing:
            raise ParseError(
                "CSE company download is missing columns "
                f"{sorted(missing)}; the spreadsheet layout may have changed."
            )
        if df.empty:
            return pd.DataFrame(columns=cls.HISTORY_COLUMNS)
        out = df[list(cls._CSE_HISTORY_COLUMN_MAP)].rename(
            columns=cls._CSE_HISTORY_COLUMN_MAP
        )
        out['DATE'] = pd.to_datetime(out['DATE']).dt.strftime('%Y-%m-%d')
        out['TRADING_CODE'] = out['TRADING_CODE'].astype(str).str.strip()
        for col in cls.HISTORY_COLUMNS[2:]:
            out[col] = pd.to_numeric(out[col], errors='coerce').astype(float)
        out['VALUE_MN'] = (out['VALUE_MN'] / 1e6).round(3)
        out = out.sort_values(
            ['DATE', 'TRADING_CODE'], ascending=[False, True]
        ).reset_index(drop=True)
        return out[cls.HISTORY_COLUMNS]

    def fetch_cse_day_end_chunk(self, start, end):
        """Download all CSE symbols for ``start..end`` (network, uncached)."""
        start_s, end_s = self._to_date(start).isoformat(), self._to_date(end).isoformat()
        resp = self.post_with_csrf(
            self.HISTORICAL_DATA_PAGE_CSE, self.DOWNLOAD_COMPANY_URL_CSE,
            {'from': start_s, 'to': end_s},
        )
        df = read_xlsx_bytes(
            resp.content, resp.headers.get('content-type', ''),
            source=f"CSE company download {start_s}..{end_s}",
        )
        return self.cse_download_to_history(df)

    @classmethod
    def _cse_chunks(cls, start, end, chunk='year'):
        """Whole calendar-year/month ``(start, end)`` pairs covering the range.

        Chunks are clipped to ``CSE_EARLIEST_DATE..today`` but **not** to the
        requested range, so the same chunk is downloaded and cached whatever
        sub-range a caller asks for; callers filter rows afterwards.
        """
        if chunk not in cls.CSE_CHUNK_SIZES:
            raise ValueError(
                f"chunk must be one of {cls.CSE_CHUNK_SIZES}, got {chunk!r}"
            )
        earliest = cls._to_date(cls.CSE_EARLIEST_DATE)
        today = datetime.date.today()
        start = max(cls._to_date(start), earliest)
        end = min(cls._to_date(end), today)
        chunks = []
        cursor = start
        while cursor <= end:
            if chunk == 'year':
                first = datetime.date(cursor.year, 1, 1)
                last = datetime.date(cursor.year, 12, 31)
            else:
                first = datetime.date(cursor.year, cursor.month, 1)
                last = datetime.date(
                    cursor.year, cursor.month,
                    calendar.monthrange(cursor.year, cursor.month)[1],
                )
            chunks.append((max(first, earliest), min(last, today)))
            cursor = last + datetime.timedelta(days=1)
        return chunks

    @staticmethod
    def _cse_chunk_is_closed(chunk):
        """A chunk that ends before today can never change again."""
        return chunk[1] < datetime.date.today()

    def _cse_cache_path(self, chunk):
        return os.path.join(
            self.cache_dir,
            self.CSE_CACHE_FILE_PATTERN.format(
                start=chunk[0].isoformat(), end=chunk[1].isoformat()
            ),
        )

    def _cse_load_chunk(self, chunk, use_cache):
        """Memory cache, then disk cache (closed chunks only). ``None`` on miss."""
        if not use_cache:
            return None
        if chunk in self._cse_chunk_cache:
            return self._cse_chunk_cache[chunk]
        if self.cache_dir and self._cse_chunk_is_closed(chunk):
            path = self._cse_cache_path(chunk)
            if os.path.exists(path):
                frame = pd.read_pickle(path)
                self._cse_chunk_cache[chunk] = frame
                return frame
        return None

    def _cse_store_chunk(self, chunk, frame, use_cache):
        if not use_cache or not self._cse_chunk_is_closed(chunk):
            return
        self._cse_chunk_cache[chunk] = frame
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            frame.to_pickle(self._cse_cache_path(chunk))

    def _cse_day_end_frame(self, start, end, chunk='year', progress=True,
                           use_cache=True):
        """All CSE symbols for ``start..end`` in the history schema."""
        start_d, end_d = self._to_date(start), self._to_date(end)
        chunks = self._cse_chunks(start_d, end_d, chunk)
        resolved, misses = {}, []
        for c in chunks:
            frame = self._cse_load_chunk(c, use_cache)
            if frame is None:
                misses.append(c)
            else:
                resolved[c] = frame
        for index, c in enumerate(misses, 1):
            self._report_progress(progress, c[0], c[1], index, len(misses))
            frame = self.fetch_cse_day_end_chunk(*c)
            self._cse_store_chunk(c, frame, use_cache)
            resolved[c] = frame
        frames = [resolved[c] for c in chunks if not resolved[c].empty]
        if not frames:
            return pd.DataFrame(columns=self.HISTORY_COLUMNS)
        out = pd.concat(frames, ignore_index=True)
        # ISO strings compare chronologically.
        mask = (out['DATE'] >= start_d.isoformat()) & (out['DATE'] <= end_d.isoformat())
        return out[mask].sort_values(
            ['DATE', 'TRADING_CODE'], ascending=[False, True]
        ).reset_index(drop=True)

    # ------------------------------------------------------------------ #
    # CSE: live prices
    # ------------------------------------------------------------------ #
    def parse_current_prices_cse(self, soup, trading_date=None, close_by_code=None):
        """Parse the CSE live table into the DSE current-price schema.

        The CSE table has no close column and no trading date, so callers pass
        ``trading_date`` and a ``close_by_code`` mapping from the same-day
        day-end download; ``CLOSEP`` falls back to ``LTP`` for codes without
        one. ``% CHANGE`` is the absolute change ``LTP - YCP``, which is what
        the DSE live feed publishes under that name. The CSE-only ``OPEN``
        column is dropped.
        """
        stock_table = soup.find("table", attrs={"id": "dataTable"})
        if stock_table is None:
            raise ParseError(
                "CSE current price table (#dataTable) not found; the page "
                "layout may have changed."
            )
        trading_date = trading_date or datetime.date.today()
        close_by_code = close_by_code or {}
        dict_list = []
        for row in stock_table.find_all("tr"):
            if row.find_all("th"):
                continue
            td_values = ["".join(td.get_text().split()) for td in row.find_all("td")]
            if len(td_values) < 10:
                continue
            code = td_values[1]
            ltp = self.parse_float(td_values[2])
            ycp = self.parse_float(td_values[6])
            dict_list.append({
                'DATE': trading_date,
                'TRADING_CODE': code,
                'LTP': ltp,
                'HIGH': self.parse_float(td_values[4]),
                'LOW': self.parse_float(td_values[5]),
                'CLOSEP': float(close_by_code.get(code, ltp)),
                'YCP': ycp,
                '% CHANGE': round(ltp - ycp, 2),
                'TRADE': self.parse_float(td_values[7]),
                'VALUE_MN': self.parse_float(td_values[8]),
                'VOLUME': self.parse_float(td_values[9]),
            })
        return dict_list

    @classmethod
    def parse_trading_date_cse(cls, html):
        """Trading date from a CSE company page ("Last Trade Date"/"Updated
        Date"), or ``None`` when the label is absent."""
        text = " ".join(BeautifulSoup(html, 'html.parser').get_text(" ").split())
        match = cls._CSE_DATE_LABEL_RE.search(text)
        if match is None:
            return None
        return parser.parse(match.group(1)).date()

    def _cse_trading_date_fallback(self):
        try:
            page = self._get(self.COMPANY_DETAILS_URL_CSE + self.CSE_DATE_REFERENCE_SYMBOL)
            found = self.parse_trading_date_cse(page.text)
        except Exception as e:  # auxiliary lookup; never block the snapshot
            print(f"Warning: could not read the CSE trading date: {e}")
            found = None
        return found or datetime.date.today()

    def _cse_day_end_or_empty(self, day):
        try:
            return self.fetch_cse_day_end_chunk(day, day)
        except StockSurferError as e:
            print(f"Warning: CSE day-end download for {day} failed: {e}")
            return pd.DataFrame(columns=self.HISTORY_COLUMNS)

    def _cse_current_context(self):
        """(trading_date, {code: close}) for the CSE live snapshot.

        Prefers today's day-end download; on a non-trading day falls back to
        the company page date and that day's download.
        """
        today = datetime.date.today()
        day_end = self._cse_day_end_or_empty(today)
        if day_end.empty:
            trading_date = self._cse_trading_date_fallback()
            if trading_date != today:
                day_end = self._cse_day_end_or_empty(trading_date)
        if not day_end.empty:
            # The exchange's own trade_date, never the machine clock.
            trading_date = self._to_date(day_end['DATE'].max())
        close_by_code = dict(zip(day_end['TRADING_CODE'], day_end['CLOSEP']))
        return trading_date, close_by_code

    # ------------------------------------------------------------------ #
    # Public DataFrame API (identical shapes for DSE and CSE)
    # ------------------------------------------------------------------ #
    def get_price_history_df(self, symbol, market='DSE', start_date=None, end_date=None):
        """Daily OHLCV history for one symbol as a DataFrame.

        Columns are :attr:`HISTORY_COLUMNS` for both markets, newest first.
        ``start_date``/``end_date`` accept a ``date``/``datetime`` or any
        parseable string.

        * DSE: bounds are sent to the day-end archive; with no dates the DSE
          server returns its default window (~2 years).
        * CSE: with no dates the **full archive** (from
          :attr:`CSE_EARLIEST_DATE`) is returned. The source is an
          all-symbols spreadsheet per calendar year, downloaded once and
          cached on this instance (and in ``cache_dir`` when set), so further
          symbols on the same instance cost no network calls.
        """
        market = self._check_market(market)
        if market == 'DSE':
            records = self.parse_price_history_dse(
                symbol, start_date=start_date, end_date=end_date
            )
            return pd.DataFrame(records)
        symbol = self._normalise_symbol(symbol)
        frame = self._cse_day_end_frame(
            start_date or self.CSE_EARLIEST_DATE,
            end_date or datetime.date.today(),
        )
        return frame[frame['TRADING_CODE'] == symbol].reset_index(drop=True)

    def get_day_end_df(self, date=None, market='DSE'):
        """Day-end OHLCV for **all** instruments on a single ``date``.

        Includes the open price (``OPENP``), unlike the live current feed.
        ``date`` defaults to today and accepts a ``date``/``datetime`` or any
        parseable string. Both markets publish day-end data only after the
        session closes, so calling this for today **before market close** (or
        for a non-trading day) returns an **empty DataFrame**.
        """
        market = self._check_market(market)
        if market == 'DSE':
            return pd.DataFrame(self.parse_day_end_dse(date))
        day = self._to_date(date) if date is not None else datetime.date.today()
        return self.fetch_cse_day_end_chunk(day, day)

    def get_day_end_range_df(self, start_date, end_date=None, market='DSE',
                             symbols=None, chunk='year', progress=True,
                             use_cache=True):
        """Day-end OHLCV for all symbols (or ``symbols``) over a date range.

        Returns :attr:`HISTORY_COLUMNS`, newest first, for both markets. This
        is the efficient way to pull many CSE symbols: the CSE source is one
        spreadsheet per ``chunk`` (``'year'`` or ``'month'``) covering every
        symbol, so pull once and split by ``TRADING_CODE``. For DSE it loops
        the day-end archive once per calendar day (slower; skips days with no
        data such as weekends).

        ``symbols``: optional iterable of trading codes to keep.
        ``progress``: ``True`` prints one line per download, ``False`` is
        silent, or a callable ``progress(chunk_start, chunk_end, index, total)``.
        ``use_cache``: ``False`` bypasses (and does not populate) the CSE
        memory/disk caches, e.g. after the exchange restated a day.
        """
        if start_date is None:
            raise ValueError("start_date is required")
        market = self._check_market(market)
        if chunk not in self.CSE_CHUNK_SIZES:
            raise ValueError(
                f"chunk must be one of {self.CSE_CHUNK_SIZES}, got {chunk!r}"
            )
        start_d = self._to_date(start_date)
        end_d = self._to_date(end_date) if end_date is not None else datetime.date.today()
        if market == 'CSE':
            frame = self._cse_day_end_frame(
                start_d, end_d, chunk=chunk, progress=progress, use_cache=use_cache
            )
        else:
            frame = self._dse_day_end_range(start_d, end_d, progress)
        if symbols is not None:
            wanted = {self._normalise_symbol(s) for s in symbols}
            frame = frame[frame['TRADING_CODE'].isin(wanted)].reset_index(drop=True)
        return frame

    def _dse_day_end_range(self, start_d, end_d, progress):
        days = [
            start_d + datetime.timedelta(days=i)
            for i in range((end_d - start_d).days + 1)
        ]
        frames = []
        for index, day in enumerate(days, 1):
            if callable(progress):
                progress(day, day, index, len(days))
            elif progress:
                print(f"DSE day-end {day} ({index}/{len(days)})")
            records = self.parse_day_end_dse(day)
            if records:
                frames.append(pd.DataFrame(records, columns=self.HISTORY_COLUMNS))
        if not frames:
            return pd.DataFrame(columns=self.HISTORY_COLUMNS)
        return pd.concat(frames, ignore_index=True).sort_values(
            ['DATE', 'TRADING_CODE'], ascending=[False, True]
        ).reset_index(drop=True)

    def get_current_price_df(self, market='DSE'):
        """Snapshot of all listed symbols' latest prices as a DataFrame.

        Columns are :attr:`CURRENT_COLUMNS` for both markets. Neither live
        feed publishes an open price; use :meth:`get_price_history_df` or
        :meth:`get_day_end_df` for ``OPENP``. For CSE, ``DATE`` and ``CLOSEP``
        come from the exchange's same-day day-end download when available
        (``CLOSEP`` falls back to ``LTP`` otherwise).
        """
        market = self._check_market(market)
        if market == 'DSE':
            page = self._get(self.CURRENT_PRICE_URL_DSE)
            records = self.parse_current_prices_dse(
                BeautifulSoup(page.text, 'html.parser')
            )
            return pd.DataFrame(records)
        page = self._get(self.CURRENT_PRICE_URL_CSE)
        soup = BeautifulSoup(page.text, 'html.parser')
        trading_date, close_by_code = self._cse_current_context()
        records = self.parse_current_prices_cse(soup, trading_date, close_by_code)
        return pd.DataFrame(records, columns=self.CURRENT_COLUMNS)

    # ------------------------------------------------------------------ #
    # File writers (thin wrappers; output layout unchanged)
    # ------------------------------------------------------------------ #
    def save_history_data(self, symbol, file_path='', file_name='history_data.csv',
                          market='DSE', start_date=None, end_date=None):
        rows = self.get_price_history_df(
            symbol, market=market, start_date=start_date, end_date=end_date
        ).to_dict('records')
        self.save_excel(dict_list=rows, csv_path=os.path.join(file_path, file_name))

    def save_current_data(self, file_path='', file_name='dsebd_current_data.csv', market='DSE'):
        rows = self.get_current_price_df(market=market).to_dict('records')
        self.save_excel(dict_list=rows, csv_path=os.path.join(file_path, file_name))

    def save_day_end_range_data(self, file_path='', file_name='day_end_range.xlsx',
                                market='DSE', start_date=None, end_date=None,
                                **kwargs):
        """Write :meth:`get_day_end_range_df` to one Excel file. ``kwargs``
        (``symbols``, ``chunk``, ``progress``, ``use_cache``) pass through."""
        rows = self.get_day_end_range_df(
            start_date, end_date=end_date, market=market, **kwargs
        ).to_dict('records')
        self.save_excel(dict_list=rows, csv_path=os.path.join(file_path, file_name))
