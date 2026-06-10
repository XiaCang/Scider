import os
import redis.asyncio as aioredis

REDIS_URL = os.getenv("REDIS_VERIFY_URL", "redis://localhost:6379/2")




def get_redis():
    # returns an async redis client. Prefer REDIS_URL, fallback to REDIS_BROKER_URL/REDIS_RESULT_BACKEND.
    return aioredis.from_url(REDIS_URL)
