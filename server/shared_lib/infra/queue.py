from .redis import redis_client
from shared_lib.pydantic_models.models import JobData
import json
from shared_lib.core.exceptions import BaseAPIException

async def ingest(job_data:JobData):
    try:
        job_json_string=json.dumps(job_data)
        await redis_client.xadd(
        "rag:jobs",
        {
            "job": job_json_string
        }
    )
        return True
    except Exception as e:
        print(e)
        raise BaseAPIException(message="Problem while ingestion",status_code=400)