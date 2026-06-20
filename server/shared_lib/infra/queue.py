from .redis import redis_client
from shared_lib.pydantic_models.models import JobData,DeleteJob,EmailJob
import json
from shared_lib.core.exceptions import BaseAPIException

async def ingest(job_data:JobData):
    print("JOB DATA TYPE:", type(job_data))
    print("JOB DATA:", job_data)
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

async def delete_document(job_data: DeleteJob):
    try:
        job_json_string=json.dumps(job_data)
        await redis_client.xadd(
        "rag:delete-jobs",
        {
            "job": job_json_string
        }
    )
        return True
    except Exception as e:
        print(e)
        raise BaseAPIException(message="Problem while ingestion",status_code=400)

async def send_email(job_data: EmailJob):
    try:
        job_json_string=json.dumps(job_data)
        await redis_client.xadd(
        "rag:sendmail-jobs",
        {
            "job": job_json_string
        }
    )
        return True
    except Exception as e:
        print(e)
        raise BaseAPIException(message="Problem while ingestion",status_code=400)