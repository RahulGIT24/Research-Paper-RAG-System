from typing import List
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from shared_lib.core.config import settings
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchParams, MatchAny, SetPayload, SetPayloadOperation

from .embed_model import EmbedModel

class QdrantVectorService:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )
        self.embed_model = EmbedModel.get_embed_model()

    def ingest_documents(
        self,
        documents: any,
        user_id: str,
        doc_id: str,
        document_hash_id: str
    ) -> bool:

        existing_found = self._scroll_all(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_hash_id",
                        match=MatchValue(value=document_hash_id)
                    )
                ]
            )
        )

        if existing_found:
            for point in existing_found:
                current_user_ids = point.payload.get("user_ids", [])
                if user_id not in current_user_ids:
                    self.client.set_payload(
                        collection_name=self.collection_name,
                        payload={"user_ids": current_user_ids + [user_id]},
                        points=[point.id]
                    )
            return True

        # new document — embed and insert
        texts = [doc['text'] for doc in documents]
        vectors = self.embed_model.get_text_embedding_batch(texts)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": doc['text'],
                    "document_hash_id": document_hash_id,
                    "page": doc['metadata'].get("page"),
                    "source": doc['metadata'].get("source"),
                    "server_file_name": doc['metadata'].get("server_file_name"),
                    "file_name": doc['metadata'].get("file_name"),
                    "user_ids": [user_id],
                    "doc_id": doc_id
                },
            )
            for doc, vector in zip(documents, vectors)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=False,
        )

        return True

    def query(self, query_embedding: List[float], user_id: str, limit: int = 5, doc_id: str | None = None):
        match_conditions = [
            FieldCondition(
                key="user_ids",
                match=MatchAny(any=[str(user_id)])
            )
        ]

        if doc_id is not None:
            match_conditions.append(
                FieldCondition(
                    key="doc_id",
                    match=MatchValue(value=str(doc_id))
                )
            )

        search_result = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_embedding,
            limit=limit,
            query_filter=Filter(must=match_conditions),
            search_params=SearchParams(hnsw_ef=128, exact=False),
            with_payload=True
        )

        return [
            {
                "id": point.id,
                "score": point.score,
                "text": point.payload.get("text"),
                "source": point.payload.get("source"),
                "page": point.payload.get("page"),
                "file_name": point.payload.get("file_name"),
                "server_file_name": point.payload.get("server_file_name"),
            }
            for point in search_result.points
        ]

    def remove_user_from_vectors(self, document_hash_id: str, user_id: str) -> bool:
        scroll_filter = Filter(
            must=[
                FieldCondition(key="document_hash_id", match=MatchValue(value=document_hash_id)),
                FieldCondition(key="user_ids", match=MatchValue(value=user_id)),
            ]
        )

        offset = None
        operations = []

        while True:
            points, offset = self.client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                scroll_filter=scroll_filter,
                with_payload=True,
                limit=1000,
                offset=offset,
            )

            for point in points:
                users = point.payload.get("user_ids", [])
                if user_id in users:
                    updated_users = [u for u in users if u != user_id]
                    operations.append(
                        SetPayloadOperation(
                            set_payload=SetPayload(
                                payload={"user_ids": updated_users},
                                points=[point.id],
                            )
                        )
                    )

            if offset is None:
                break

        if operations:
            self.client.batch_update_points(
                collection_name=settings.QDRANT_COLLECTION,
                update_operations=operations,
            )
        print("userids deleted")
        return True

    def grant_user_access(self, document_hash_id: str, user_id: str) -> bool:
        all_points = self._scroll_all(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_hash_id",
                        match=MatchValue(value=document_hash_id)
                    )
                ]
            )
        )

        if not all_points:
            return False

        for point in all_points:
            current_user_ids = point.payload.get("user_ids", [])
            if user_id not in current_user_ids:
                self.client.set_payload(
                    collection_name=self.collection_name,
                    payload={"user_ids": current_user_ids + [user_id]},
                    points=[point.id]
                )

        return True

    def _scroll_all(self, filter: Filter) -> list:
        all_points = []
        offset = None

        while True:
            batch, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter,
                with_payload=True,
                limit=100,
                offset=offset
            )

            if not batch:
                break

            all_points.extend(batch)

            if next_offset is None:
                break

            offset = next_offset

        return all_points