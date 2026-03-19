from __future__ import annotations

from urllib.parse import urlparse

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

DEFAULT_TIMEOUT: float = 30.0
DEFAULT_MAX_RETRIES: int = 3


def _should_retry(exc: BaseException) -> bool:
    """Retry only on connection / network errors, not HTTP status errors."""
    return isinstance(exc, httpx.RequestError)


@retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_should_retry),
)
async def send_request(
    method: str,
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs,
) -> httpx.Response:
    """Send an async HTTP request with automatic retry on transient errors.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        url: Target URL. Must use http or https scheme.
        timeout: Request timeout in seconds (default 30).
        **kwargs: Additional arguments forwarded to ``httpx.AsyncClient.request``.

    Returns:
        The ``httpx.Response`` object.

    Raises:
        ValueError: If the URL scheme is not http/https.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(method.upper(), url, **kwargs)
        return response
