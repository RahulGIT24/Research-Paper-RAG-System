from shared_lib.chunking.SemanticChunker import SemanticChunker
import json
from shared_lib.infra.redis import redis_client,redis_instance
import json
from .process_job import ProcessJob
import asyncio
from shared_lib.qdrant.vector_store import QdrantVectorService
from shared_lib.db.session import SessionLocal

# should be run as a module in terminal
# uv run python -m workers.ingestion_worker

STREAM = "rag:jobs"
GROUP = "rag-workers"
CONSUMER = "worker-1"

async def run_worker(processor:ProcessJob):
    await redis_instance.create_document_consumer_groups()
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
                try:
                    job_string = message['job']
                    job_dict = json.loads(job_string)
                    # print(job_dict)
                    
                    processor.process_job(job_dict)
                    await redis_client.xack(
                        STREAM,
                        GROUP,
                        message_id
                    )
                except Exception as e:
                    print(f"Job failed: {e}")


if __name__ == "__main__":
    import sys
    try:
        splitter = SemanticChunker().get_semantic_splitter()

        qdrant = QdrantVectorService()

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