from __future__ import annotations

from urllib.parse import urlparse

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

DEFAULT_TIMEOUT: float = 30.0
DEFAULT_MAX_RETRIES: int = 3

# Shared client — connection pooling across all requests
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient()
    return _client


def _should_retry(exc: BaseException) -> bool:
    """Retry only on connection / network errors, not HTTP status errors."""
    return isinstance(exc, httpx.RequestError)


async def send_request(
    method: str,
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    **kwargs,
) -> httpx.Response:
    """Send an async HTTP request with automatic retry on transient errors.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        url: Target URL. Must use http or https scheme.
        timeout: Request timeout in seconds (default 30).
        max_retries: Maximum number of attempts on transient errors (default 3).
        **kwargs: Additional arguments forwarded to ``httpx.AsyncClient.request``.

    Returns:
        The ``httpx.Response`` object.

    Raises:
        ValueError: If the URL scheme is not http/https.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_should_retry),
        reraise=True,
    )
    async def _do_request() -> httpx.Response:
        return await _get_client().request(method.upper(), url, timeout=timeout, **kwargs)

    return await _do_request()


async def close() -> None:
    """Close the shared HTTP client, releasing connections."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None
