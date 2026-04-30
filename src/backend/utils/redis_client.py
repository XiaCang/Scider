import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")


def get_redis():
    # returns a redis client (singleton-like creation handled by redis-py)
    return aioredis.from_url(REDIS_URL)
