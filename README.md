# httplite

Lightweight async HTTP client with automatic retry on transient errors.
Built on [httpx](https://www.python-httpx.org/) and [tenacity](https://tenacity.readthedocs.io/).

## Installation

```bash
pip install httplite
```

## Quick start

```python
import asyncio
from httplite import send_request

async def main():
    # Simple GET
    resp = await send_request("GET", "https://httpbin.org/get")
    print(resp.status_code)
    print(resp.json())

    # POST with JSON body
    resp = await send_request("POST", "https://httpbin.org/post", json={"key": "value"})
    print(resp.json())

    # Custom timeout (seconds)
    resp = await send_request("GET", "https://httpbin.org/delay/2", timeout=10)

asyncio.run(main())
```

## Features

- **Async-first** – uses `httpx.AsyncClient` under the hood.
- **Automatic retry** – retries up to 3 times with exponential backoff on transient connection errors (`httpx.RequestError`). HTTP error status codes (4xx, 5xx) are **not** retried.
- **Configurable timeout** – defaults to 30 seconds; override per request.
- **Minimal API** – a single `send_request()` function. Any extra keyword arguments are forwarded directly to `httpx.AsyncClient.request`.

## API

### `send_request(method, url, *, timeout=30.0, **kwargs)`

| Parameter | Type | Description |
|-----------|-------|-------------|
| `method` | `str` | HTTP method (`GET`, `POST`, `PUT`, `DELETE`, etc.) |
| `url` | `str` | Target URL (must use `http` or `https` scheme) |
| `timeout` | `float` | Request timeout in seconds (default `30.0`) |
| `**kwargs` | | Forwarded to `httpx.AsyncClient.request` (e.g. `json`, `headers`, `params`) |

**Returns:** `httpx.Response`

**Raises:** `ValueError` if the URL scheme is not `http` or `https`.

## Running tests

```bash
pip install -e ".[test]"
pytest
```

## License

MIT