import redis.asyncio as redis
from shared_lib.core.config import settings
from redis.exceptions import ResponseError

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(host=settings.REDIS_HOST,port=settings.REDIS_PORT,decode_responses=True)
    async def create_consumer_groups(self):
        try:
            await self.client.xgroup_create(
                "rag:jobs",
                "rag-workers",
                id="0",
                mkstream=True
            )
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                pass
            else:
                raise

redis_instance = RedisClient()
redis_client = redis_instance.client 