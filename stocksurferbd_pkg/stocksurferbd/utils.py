#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Shared parsing helpers, exceptions and HTTP base for the data scrapers."""

import io
import os
import re
import tempfile

import pandas as pd
import requests
import certifi
import urllib3


# DSE moved its new website to www.dsebd.org (a Next.js app with different
# routes) in Sep 2026; the legacy pages every DSE parser depends on are still
# served, unchanged, from old.dsebd.org.
DSE_BASE_URL = 'https://old.dsebd.org'

# old.dsebd.org omits the intermediate certificate from its TLS handshake, so a
# default ``verify=True`` request fails with "unable to get local issuer
# certificate". The missing intermediate (fetched from the leaf certificate's
# AIA URL, chains to the USERTrust root in certifi) is shipped here and
# appended to certifi's bundle, so verification stays on.
# SHA-256 8C:54:C3:34:B6:6B:A4:E4:26:77:2A:F4:A3:F9:13:6C:19:A1:AE:C7:29:FD:B2:8C:53:5C:07:A5:A4:EF:22:E0
_SECTIGO_DV_R36_PEM = """\
-----BEGIN CERTIFICATE-----
MIIGTDCCBDSgAwIBAgIQOXpmzCdWNi4NqofKbqvjsTANBgkqhkiG9w0BAQwFADBf
MQswCQYDVQQGEwJHQjEYMBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTYwNAYDVQQD
Ey1TZWN0aWdvIFB1YmxpYyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gUm9vdCBSNDYw
HhcNMjEwMzIyMDAwMDAwWhcNMzYwMzIxMjM1OTU5WjBgMQswCQYDVQQGEwJHQjEY
MBYGA1UEChMPU2VjdGlnbyBMaW1pdGVkMTcwNQYDVQQDEy5TZWN0aWdvIFB1Ymxp
YyBTZXJ2ZXIgQXV0aGVudGljYXRpb24gQ0EgRFYgUjM2MIIBojANBgkqhkiG9w0B
AQEFAAOCAY8AMIIBigKCAYEAljZf2HIz7+SPUPQCQObZYcrxLTHYdf1ZtMRe7Yeq
RPSwygz16qJ9cAWtWNTcuICc++p8Dct7zNGxCpqmEtqifO7NvuB5dEVexXn9RFFH
12Hm+NtPRQgXIFjx6MSJcNWuVO3XGE57L1mHlcQYj+g4hny90aFh2SCZCDEVkAja
EMMfYPKuCjHuuF+bzHFb/9gV8P9+ekcHENF2nR1efGWSKwnfG5RawlkaQDpRtZTm
M64TIsv/r7cyFO4nSjs1jLdXYdz5q3a4L0NoabZfbdxVb+CUEHfB0bpulZQtH1Rv
38e/lIdP7OTTIlZh6OYL6NhxP8So0/sht/4J9mqIGxRFc0/pC8suja+wcIUna0HB
pXKfXTKpzgis+zmXDL06ASJf5E4A2/m+Hp6b84sfPAwQ766rI65mh50S0Di9E3Pn
2WcaJc+PILsBmYpgtmgWTR9eV9otfKRUBfzHUHcVgarub/XluEpRlTtZudU5xbFN
xx/DgMrXLUAPaI60fZ6wA+PTAgMBAAGjggGBMIIBfTAfBgNVHSMEGDAWgBRWc1hk
lfmSGrASKgRieaFAFYghSTAdBgNVHQ4EFgQUaMASFhgOr872h6YyV6NGUV3LBycw
DgYDVR0PAQH/BAQDAgGGMBIGA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0lBBYwFAYI
KwYBBQUHAwEGCCsGAQUFBwMCMBsGA1UdIAQUMBIwBgYEVR0gADAIBgZngQwBAgEw
VAYDVR0fBE0wSzBJoEegRYZDaHR0cDovL2NybC5zZWN0aWdvLmNvbS9TZWN0aWdv
UHVibGljU2VydmVyQXV0aGVudGljYXRpb25Sb290UjQ2LmNybDCBhAYIKwYBBQUH
AQEEeDB2ME8GCCsGAQUFBzAChkNodHRwOi8vY3J0LnNlY3RpZ28uY29tL1NlY3Rp
Z29QdWJsaWNTZXJ2ZXJBdXRoZW50aWNhdGlvblJvb3RSNDYucDdjMCMGCCsGAQUF
BzABhhdodHRwOi8vb2NzcC5zZWN0aWdvLmNvbTANBgkqhkiG9w0BAQwFAAOCAgEA
YtOC9Fy+TqECFw40IospI92kLGgoSZGPOSQXMBqmsGWZUQ7rux7cj1du6d9rD6C8
ze1B2eQjkrGkIL/OF1s7vSmgYVafsRoZd/IHUrkoQvX8FZwUsmPu7amgBfaY3g+d
q1x0jNGKb6I6Bzdl6LgMD9qxp+3i7GQOnd9J8LFSietY6Z4jUBzVoOoz8iAU84OF
h2HhAuiPw1ai0VnY38RTI+8kepGWVfGxfBWzwH9uIjeooIeaosVFvE8cmYUB4TSH
5dUyD0jHct2+8ceKEtIoFU/FfHq/mDaVnvcDCZXtIgitdMFQdMZaVehmObyhRdDD
4NQCs0gaI9AAgFj4L9QtkARzhQLNyRf87Kln+YU0lgCGr9HLg3rGO8q+Y4ppLsOd
unQZ6ZxPNGIfOApbPVf5hCe58EZwiWdHIMn9lPP6+F404y8NNugbQixBber+x536
WrZhFZLjEkhp7fFXf9r32rNPfb74X/U90Bdy4lzp3+X1ukh1BuMxA/EEhDoTOS3l
7ABvc7BYSQubQ2490OcdkIzUh3ZwDrakMVrbaTxUM2p24N6dB+ns2zptWCva6jzW
r8IWKIMxzxLPv5Kt3ePKcUdvkBU/smqujSczTzzSjIoR5QqQA6lN1ZRSnuHIWCvh
JEltkYnTAH41QJ6SAWO66GrrUESwN/cgZzL4JLEqz1Y=
-----END CERTIFICATE-----
"""

_ca_bundle_path = None


def ca_bundle():
    """Path to certifi's CA bundle plus the intermediates DSE fails to send.

    Written once per process to a temp file, since ``requests`` needs a path.
    """
    global _ca_bundle_path
    if _ca_bundle_path is None or not os.path.exists(_ca_bundle_path):
        with open(certifi.where(), encoding='ascii') as fh:
            bundle = fh.read()
        fd, path = tempfile.mkstemp(prefix='stocksurferbd-ca-', suffix='.pem')
        with os.fdopen(fd, 'w', encoding='ascii') as fh:
            fh.write(bundle.rstrip('\n') + '\n' + _SECTIGO_DV_R36_PEM)
        _ca_bundle_path = path
    return _ca_bundle_path


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

        loader = PriceData(verify=False)          # skip TLS verification
        loader = FundamentalData(session=my_sess, timeout=60)

    ``verify=True`` (the default) verifies against :func:`ca_bundle`, which
    completes DSE's broken certificate chain; a path or ``False`` is passed
    to ``requests`` as given. Defaults (a fresh session, 30s timeout) keep the
    previous behaviour, so ``PriceData()`` / ``FundamentalData()`` / ``BlockTradeData()``
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

    def _verify_arg(self):
        return ca_bundle() if self.verify is True else self.verify

    def _get(self, url):
        return self.session.get(url, timeout=self.timeout, verify=self._verify_arg())

    def _post(self, url, data, headers=None):
        return self.session.post(
            url, data=data, timeout=self.timeout, verify=self._verify_arg(),
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
