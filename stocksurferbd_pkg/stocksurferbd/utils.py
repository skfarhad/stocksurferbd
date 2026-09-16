#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Shared parsing helpers, exceptions and HTTP base for the data scrapers."""

import io
import re

import pandas as pd
import requests
import urllib3


class StockSurferError(Exception):
    """Base error for the library."""


class FetchError(StockSurferError):
    """Network/HTTP failure fetching a source page."""


class ParseError(StockSurferError):
    """Page fetched, but an expected table/field was missing or malformed."""


def parse_float(str_val):
    new_val = str_val.replace(',', '').replace('--', '0')
    return float(new_val)


def parse_int(str_val):
    new_val = str_val.replace(',', '').replace('--', '0')
    return int(new_val)


# xlsx files are zip archives; the first two bytes are the zip magic number.
_ZIP_MAGIC = b'PK'


def read_xlsx_bytes(content, content_type='', source='download'):
    """Parse an xlsx HTTP body into a DataFrame.

    The CSE download endpoints answer with an HTML error page (HTTP 200) when
    the request is malformed, so the body is checked for the zip signature
    before it is handed to pandas. Raises :class:`ParseError` naming the
    ``source`` and quoting the start of the body otherwise.
    """
    if not content or not content.startswith(_ZIP_MAGIC):
        snippet = (content or b'')[:200].decode('utf-8', 'replace')
        kind = (content_type or 'unknown content type').split(';')[0].strip()
        raise ParseError(
            f"Expected a spreadsheet from {source} but got {kind}: {snippet!r}"
        )
    return pd.read_excel(io.BytesIO(content), engine='openpyxl')


class HttpScraper(object):
    """Base class providing a shared, configurable HTTP fetch.

    All scrapers fetch from the DSE/CSE public sites. This centralises the
    request options so callers can control TLS verification, reuse a
    ``requests.Session``, and set a timeout:

        loader = PriceData(verify=False)          # DSE's cert chain is
                                                  # incomplete in some envs
        loader = FundamentalData(session=my_sess, timeout=60)

    Defaults (``verify=True``, a fresh session, 30s timeout) keep the previous
    behaviour, so ``PriceData()`` / ``FundamentalData()`` / ``BlockTradeData()``
    work unchanged.
    """

    DEFAULT_TIMEOUT = 30

    # CSE guards every form POST with a per-page CSRF token, published either
    # as a hidden input or (on the home page) inside inline JavaScript.
    CSRF_FIELD_CSE = 'csrf_cse_token'
    _CSRF_INPUT_RE = re.compile(
        r'name=["\']csrf_cse_token["\']\s+value=["\']([0-9a-f]+)["\']'
    )
    _CSRF_JS_RE = re.compile(
        r"csrf_cse_token['\"]?\s*[:=]\s*['\"]([0-9a-f]+)['\"]"
    )

    def __init__(self, verify=True, session=None, timeout=None):
        self.verify = verify
        self.timeout = self.DEFAULT_TIMEOUT if timeout is None else timeout
        self.session = session if session is not None else requests.Session()
        if not self.verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get(self, url):
        return self.session.get(url, timeout=self.timeout, verify=self.verify)

    def _post(self, url, data, headers=None):
        return self.session.post(
            url, data=data, timeout=self.timeout, verify=self.verify,
            headers=headers,
        )

    def get_csrf_token(self, page_url):
        """Fetch ``page_url`` and return the CSE CSRF token it embeds."""
        try:
            page = self._get(page_url)
            page.raise_for_status()
        except requests.RequestException as e:
            raise FetchError(f"Failed to fetch {page_url}: {e}") from e
        match = (self._CSRF_INPUT_RE.search(page.text)
                 or self._CSRF_JS_RE.search(page.text))
        if match is None:
            raise ParseError(
                f"No {self.CSRF_FIELD_CSE} found on {page_url}; the page "
                "layout may have changed."
            )
        return match.group(1)

    def post_with_csrf(self, page_url, action_url, data, token=None):
        """POST ``data`` to ``action_url`` with a CSE CSRF token attached.

        The token is read from ``page_url`` (same session, so the cookie the
        token is bound to travels with the POST) unless ``token`` is given,
        which lets callers fetch it once for several POSTs. ``Referer`` is set
        to ``page_url`` as the site expects.
        """
        if token is None:
            token = self.get_csrf_token(page_url)
        payload = dict(data)
        payload[self.CSRF_FIELD_CSE] = token
        try:
            resp = self._post(action_url, payload, headers={'Referer': page_url})
            resp.raise_for_status()
        except requests.RequestException as e:
            raise FetchError(f"Failed to POST {action_url}: {e}") from e
        return resp
