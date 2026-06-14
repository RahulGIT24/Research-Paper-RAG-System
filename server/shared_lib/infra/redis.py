import redis.asyncio as redis
from shared_lib.core.config import settings
from redis.exceptions import ResponseError

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(host=settings.REDIS_HOST,port=settings.REDIS_PORT,decode_responses=True)
    async def create_document_consumer_groups(self):
        try:
            await self.client.xgroup_create(
                "rag:jobs",
                "rag-workers",
                id="0",
                mkstream=True
            )
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    async def create_delete_consumer_groups(self):
        try:
            await self.client.xgroup_create(
                "rag:delete-jobs",
                "rag-delete-workers",
                id="0",
                mkstream=True
            )
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
    async def create_email_consumer_groups(self):
        try:
            await self.client.xgroup_create(
                "rag:sendmail-jobs",
                "rag-sendmail-workers",
                id="0",
                mkstream=True
            )
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

redis_instance = RedisClient()
redis_client = redis_instance.client 