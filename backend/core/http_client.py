import httpx
from typing import Optional


def create_client(timeout: float = 30, max_retries: int = 2) -> httpx.AsyncClient:
    transport = httpx.AsyncHTTPTransport(retries=max_retries)
    return httpx.AsyncClient(transport=transport, timeout=timeout)
