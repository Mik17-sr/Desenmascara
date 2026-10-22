"""In-memory sliding-window rate limit; enough for one API process."""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0):
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            raise HTTPException(status_code=429, detail="Demasiadas consultas. Intenta de nuevo en un minuto.")
        hits.append(now)


public_limiter = RateLimiter(limit=20)
bot_user_limiter = RateLimiter(limit=12)
# «Reportar» sends one call per number or link of the message: it must not use up the analyses.
report_limiter = RateLimiter(limit=40)


async def limit_by_ip(request: Request) -> None:
    public_limiter.check(request.client.host if request.client else "desconocido")
