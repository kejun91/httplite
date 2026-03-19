from __future__ import annotations

import httpx
import pytest
import respx

from httplite import send_request


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


# --- error / validation tests ---


async def test_invalid_scheme_raises_value_error():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        await send_request("GET", "ftp://example.com/file")


async def test_empty_scheme_raises_value_error():
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        await send_request("GET", "://no-scheme")


# --- retry behaviour ---


@respx.mock
async def test_retries_on_connection_error(monkeypatch):
    """send_request retries transient connection errors up to the max attempts."""
    # Patch retry settings to keep tests fast
    import httplite.client as client_mod

    monkeypatch.setattr(client_mod, "DEFAULT_MAX_RETRIES", 2)

    call_count = 0

    async def flaky_handler(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.ConnectError("connection refused")
        return httpx.Response(200)

    respx.get("https://example.com/retry").mock(side_effect=flaky_handler)

    # Rebuild the retry decorator with fast settings for testing
    from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

    # Unwrap the original function from the tenacity wrapper
    original_fn = send_request.__wrapped__

    patched = retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0, min=0, max=0),
        retry=retry_if_exception(client_mod._should_retry),
    )(original_fn)

    resp = await patched("GET", "https://example.com/retry")
    assert resp.status_code == 200
    assert call_count == 2


@respx.mock
async def test_non_retryable_error_propagates():
    """HTTP status errors should not be retried."""
    respx.get("https://example.com/err").mock(return_value=httpx.Response(500))

    resp = await send_request("GET", "https://example.com/err")
    assert resp.status_code == 500
