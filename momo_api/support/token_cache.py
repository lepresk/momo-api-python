import time
from typing import Optional


class TokenCache:
    """In-memory token cache with TTL expiry."""

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def get(self) -> Optional[str]:
        if self._token is None or time.monotonic() >= self._expires_at:
            self._token = None
            return None
        return self._token

    def set(self, token: str, expires_in: int) -> None:
        self._token = token
        self._expires_at = time.monotonic() + max(0, expires_in - 60)
