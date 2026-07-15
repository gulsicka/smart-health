import redis.asyncio as aioredis
from .config import settings



async def get_redis():
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True) # decodes responses to strings instead of bytes, no need to use .decode() everywhere
    try:
        yield client
    finally:
        await client.close()