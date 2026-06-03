import asyncio
from pathlib import Path
from shared_lib.infra.redis import redis_client
from shared_lib.db.session import SessionLocal
from shared_lib.models import Document
from shared_lib.qdrant.vector_store import QdrantVectorService

qdrant = QdrantVectorService()

STREAM_NAME = "rag:delete-jobs"
GROUP_NAME = "rag-delete-workers"
CONSUMER_NAME = "delete-worker-1"


async def process_delete_job(fields: dict):
    document_id = fields["document_id"]
    file_path = fields["file_path"]

    db = SessionLocal()

    try:
        print(f"Processing delete job for {document_id}")

        qdrant.delete_vectors(document_id)
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if document:
            db.delete(document)

        file = Path(file_path)

        if file.exists():
            file.unlink()
            print(f"Deleted file: {file_path}")

        print(
            f"Delete completed for document {document_id}"
        )

    except Exception as e:
        db.rollback()
        print(
            f"Delete failed for {document_id}: {str(e)}"
        )
        raise

    finally:
        db.close()


async def consume_delete_jobs():
    print("Delete worker started")

    while True:
        try:
            messages = await redis_client.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={
                    STREAM_NAME: ">"
                },
                count=10,
                block=5000
            )

            if not messages:
                continue

            for stream_name, entries in messages:
                for message_id, fields in entries:
                    try:
                        await process_delete_job(fields)

                        await redis_client.xack(
                            STREAM_NAME,
                            GROUP_NAME,
                            message_id
                        )

                    except Exception as e:
                        print(
                            f"Failed processing {message_id}: {e}"
                        )

        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(consume_delete_jobs())