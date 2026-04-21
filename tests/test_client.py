from __future__ import annotations

import httpx
import pytest
import respx

from httplite import send_request
from httplite.client import close, _get_client


@pytest.fixture(autouse=True)
async def _reset_client():
    """Ensure a fresh client for each test."""
    yield
    await close()


# --- happy-path tests ---


@respx.mock
async def test_get_returns_response():
    respx.get("https://example.com/data").mock(return_value=httpx.Response(200, json={"ok": True}))

    resp = await send_request("GET", "https://example.com/data")

    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@respx.mock
async def test_post_with_json_body():
    respx.post("https://example.com/items").mock(return_value=httpx.Response(201))

    resp = await send_request("POST", "https://example.com/items", json={"name": "widget"})

    assert resp.status_code == 201


@respx.mock
async def test_method_is_uppercased():
    route = respx.get("https://example.com/ping").mock(return_value=httpx.Response(200))

    await send_request("get", "https://example.com/ping")

    assert route.called


@respx.mock
async def test_custom_headers_forwarded():
    route = respx.get("https://example.com/h").mock(return_value=httpx.Response(200))

    await send_request("GET", "https://example.com/h", headers={"X-Custom": "val"})

    assert route.calls[0].request.headers["x-custom"] == "val"


# --- connection pooling ---


@respx.mock
async def test_shared_client_reused():
    """Multiple requests reuse the same underlying client."""
    respx.get("https://example.com/a").mock(return_value=httpx.Response(200))
    respx.get("https://example.com/b").mock(return_value=httpx.Response(200))

    await send_request("GET", "https://example.com/a")
    client_after_first = _get_client()

    await send_request("GET", "https://example.com/b")
    client_after_second = _get_client()

    assert client_after_first is client_after_second


async def test_close_releases_client():
    """close() shuts down the shared client."""
    client = _get_client()
    assert not client.is_closed

    await close()

    assert client.is_closed


# --- error / validation tests ---


async def test_invalid_scheme_raises_value_error():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        await send_request("GET", "ftp://example.com/file")


async def test_empty_scheme_raises_value_error():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        await send_request("GET", "://no-scheme")


# --- retry behaviour ---


@respx.mock
async def test_retries_on_connection_error():
    """send_request retries transient connection errors up to max_retries."""
    call_count = 0

    async def flaky_handler(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.ConnectError("connection refused")
        return httpx.Response(200)

    respx.get("https://example.com/retry").mock(side_effect=flaky_handler)

    resp = await send_request("GET", "https://example.com/retry", max_retries=3)
    assert resp.status_code == 200
    assert call_count == 2


@respx.mock
async def test_max_retries_configurable():
    """max_retries=1 means no retry — fails immediately."""
    respx.get("https://example.com/fail").mock(side_effect=httpx.ConnectError("refused"))

    with pytest.raises(httpx.ConnectError):
        await send_request("GET", "https://example.com/fail", max_retries=1)


@respx.mock
async def test_non_retryable_error_propagates():
    """HTTP status errors should not be retried."""
    respx.get("https://example.com/err").mock(return_value=httpx.Response(500))

    resp = await send_request("GET", "https://example.com/err")
    assert resp.status_code == 500
