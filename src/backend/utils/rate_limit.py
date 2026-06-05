import logging
from typing import Tuple

logger = logging.getLogger(__name__)


async def incr_and_check(r, key: str, limit: int, period: int) -> Tuple[bool, int]:
    """Increment counter stored at `key` (Redis) and return (is_limited, current_count).

    - r: aioredis client
    - key: redis key
    - limit: allowed attempts (int)
    - period: expiry seconds for the counter
    """
    try:
        # atomic increment
        count = await r.incr(key)
        if count == 1:
            # set expiry only for first increment
            try:
                await r.expire(key, period)
            except Exception:
                # best-effort; continue even if expire fails
                logger.exception("failed to set expiry on rate-limit key")
        return (count > limit, count)
    except Exception:
        logger.exception("redis rate limit check failed")
        # when redis fails, do not block requests — treat as not limited
        return (False, 0)
