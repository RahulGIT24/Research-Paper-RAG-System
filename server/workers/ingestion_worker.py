from shared_lib.chunking.SemanticChunker import SemanticChunker
import json
from shared_lib.infra.redis import redis_client
import json
from .process_job import ProcessJob
import asyncio
from shared_lib.db.session import get_db
from shared_lib.qdrant.vector_store import QdrantVectorService
from shared_lib.core.config import settings
from shared_lib.db.session import SessionLocal

# should be run as a module in terminal
# uv run python -m workers.ingestion_worker

STREAM = "rag:jobs"
GROUP = "rag-workers"
CONSUMER = "worker-1"

async def run_worker(processor:ProcessJob):

    while True:
        response = await redis_client.xreadgroup(
            GROUP,
            CONSUMER,
            {STREAM: ">"},
            count=1,
            block=5000
        )
        if not response:
            continue
        for stream, messages in response:
            for message_id, message in messages:
                job_string = message['job']
                job_dict = json.loads(job_string)
                # print(job_dict)
                
                processor.process_job(job_dict)

if __name__ == "__main__":
    import sys
    try:
        splitter = SemanticChunker()

        qdrant = QdrantVectorService(
            qdrant_url=settings.QDRANT_URL,
            collection_name=settings.QDRANT_COLLECTION,
            api_key=settings.QDRANT_API_KEY
        )

        processor = ProcessJob(
            redis_client=redis_client,
            splitter=splitter,
            qdrant_service=qdrant,
            session_factory=SessionLocal  
        )

        asyncio.run(run_worker(processor))
    except KeyboardInterrupt:
        print("\n[!] Keystroke 'Ctrl+C' detected! Cleaning up resources...")
        sys.exit(0)