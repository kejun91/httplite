"""httplite - Lightweight async HTTP client with automatic retry."""

from httplite.client import close, send_request

__all__ = ["send_request", "close"]
