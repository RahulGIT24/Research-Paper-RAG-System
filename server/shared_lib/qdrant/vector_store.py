from typing import List
import uuid

from llama_index.core import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from shared_lib.core.config import settings
from qdrant_client.models import Filter, FieldCondition, MatchValue,SearchParams

from .embed_model import EmbedModel

class QdrantVectorService:
    def __init__(
        self,
    ):
        self.collection_name = settings.QDRANT_COLLECTION

        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
        )

        self.embed_model = EmbedModel.get_embed_model()

    def ingest_documents(
        self,
        documents: any,
        user_id:str,
        doc_id:str
    ) -> bool:
        # [{'text': 'My name is rahul', 'metadata': {'page': 0}}]

        if not documents:
            return True

        texts = [doc['text'] for doc in documents]

        vectors = self.embed_model.get_text_embedding_batch(
            texts
        )

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": doc['text'],
                    "page": doc['metadata'].get("page"),
                    "source": doc['metadata'].get("source"),
                    "file_path": doc['metadata'].get("file_path"),
                    "file_name": doc['metadata'].get("file_name"),
                    "user_id":user_id,
                    "doc_id":doc_id
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

    def query(self,query_embedding:List[float],user_id:str,limit:int=5):
        search_result = self.client.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=query_embedding,
            limit=limit,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_id))
                    )
                ]
            ),
            search_params=SearchParams(hnsw_ef=128, exact=False),
            with_payload=True
        )
        results = []
        for point in search_result.points:
            results.append({
                "id": point.id,
                "score": point.score,
                "text": point.payload.get("text"),
                "source": point.payload.get("source"),
                "page": point.payload.get("page"),
                "file_path": point.payload.get("file_path"),
                "file_name": point.payload.get("file_name"),
            })
        return results
    
    def delete_vectors(self,doc_id:str):
        self.client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=str(doc_id))
                    )
                ]
            )
        )
        return True