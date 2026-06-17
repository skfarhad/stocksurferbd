#!/usr/bin/env python

__author__ = "Sk Farhad"
__copyright__ = "Copyright (c) 2024 The Python Packaging Authority"

"""Shared parsing helpers and HTTP base for the data scrapers."""

import requests
import urllib3


def parse_float(str_val):
    new_val = str_val.replace(',', '').replace('--', '0')
    return float(new_val)


def parse_int(str_val):
    new_val = str_val.replace(',', '').replace('--', '0')
    return int(new_val)


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

    def __init__(self, verify=True, session=None, timeout=None):
        self.verify = verify
        self.timeout = self.DEFAULT_TIMEOUT if timeout is None else timeout
        self.session = session if session is not None else requests.Session()
        if not self.verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get(self, url):
        return self.session.get(url, timeout=self.timeout, verify=self.verify)
