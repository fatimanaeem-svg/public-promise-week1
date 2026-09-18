import time
from collections import defaultdict, deque

from . import config

_hits: dict[str, deque] = defaultdict(deque)


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - config.RATE_LIMIT_WINDOW_SECONDS
    hits = _hits[ip]
    while hits and hits[0] < window_start:
        hits.popleft()
    if len(hits) >= config.RATE_LIMIT_MAX_REQUESTS:
        return True
    hits.append(now)
    return False
