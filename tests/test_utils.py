"""Tests for the shared HTTP helpers and exceptions in stocksurferbd.utils."""

import re

import pytest
import requests

from stocksurferbd import FetchError, ParseError
from stocksurferbd.utils import HttpScraper, read_xlsx_bytes


class _Resp:
    def __init__(self, text="", content=None, status=200, content_type="text/html"):
        self.text = text
        self.content = text.encode() if content is None else content
        self.status_code = status
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class _Session:
    """Minimal stand-in for requests.Session recording every call."""

    def __init__(self, get_resp=None, post_resp=None):
        self.get_resp = get_resp or _Resp()
        self.post_resp = post_resp or _Resp(text="ok")
        self.gets = []
        self.posts = []

    def get(self, url, **kwargs):
        self.gets.append({"url": url, **kwargs})
        return self.get_resp

    def post(self, url, data=None, headers=None, **kwargs):
        self.posts.append({"url": url, "data": data, "headers": headers, **kwargs})
        return self.post_resp


def test_post_with_csrf_sends_token_and_referer(cse_historicaldata_page_html):
    sess = _Session(get_resp=_Resp(text=cse_historicaldata_page_html))
    scraper = HttpScraper(session=sess, verify=False, timeout=7)

    scraper.post_with_csrf("https://x/page", "https://x/action", {"from": "2026-01-01"})

    assert sess.gets[0]["url"] == "https://x/page"
    post = sess.posts[0]
    assert post["url"] == "https://x/action"
    assert post["data"]["from"] == "2026-01-01"
    assert re.fullmatch(r"[0-9a-f]+", post["data"]["csrf_cse_token"])
    assert post["headers"] == {"Referer": "https://x/page"}
    # HTTP options are honoured on the POST as well as the GET.
    assert post["verify"] is False and post["timeout"] == 7


def test_post_with_csrf_reads_token_from_inline_js():
    html = "<script>$.post(url, { selected_index: x, csrf_cse_token: 'abc123' })</script>"
    sess = _Session(get_resp=_Resp(text=html))
    HttpScraper(session=sess).post_with_csrf("https://x/", "https://x/a", {})
    assert sess.posts[0]["data"]["csrf_cse_token"] == "abc123"


def test_post_with_csrf_reuses_given_token():
    sess = _Session()
    HttpScraper(session=sess).post_with_csrf("https://x/page", "https://x/a", {}, token="feed")
    assert sess.gets == []  # no page fetch when a token is supplied
    assert sess.posts[0]["data"]["csrf_cse_token"] == "feed"


def test_post_with_csrf_missing_token_raises():
    sess = _Session(get_resp=_Resp(text="<html><body>no form</body></html>"))
    with pytest.raises(ParseError):
        HttpScraper(session=sess).post_with_csrf("https://x/page", "https://x/a", {})
    assert sess.posts == []


def test_post_with_csrf_http_error_raises_fetch_error(cse_historicaldata_page_html):
    sess = _Session(
        get_resp=_Resp(text=cse_historicaldata_page_html),
        post_resp=_Resp(text="boom", status=500),
    )
    with pytest.raises(FetchError):
        HttpScraper(session=sess).post_with_csrf("https://x/page", "https://x/a", {})


def test_read_xlsx_bytes_rejects_html():
    with pytest.raises(ParseError) as exc:
        read_xlsx_bytes(b"<html>error page</html>", "text/html; charset=UTF-8", source="company download")
    assert "company download" in str(exc.value)
    assert "text/html" in str(exc.value)


def test_read_xlsx_bytes_parses_download(cse_day_end_bytes):
    df = read_xlsx_bytes(cse_day_end_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert {"trade_date", "company_code", "open_price", "close_price"} <= set(df.columns)
    assert len(df) > 300
