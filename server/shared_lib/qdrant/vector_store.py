from typing import List
import uuid

from llama_index.core import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from .embed_model import EmbedModel


class QdrantVectorService:

    def __init__(
        self,
        qdrant_url: str,
        collection_name: str,
        api_key: str | None = None,
    ):
        self.collection_name = collection_name

        self.client = QdrantClient(
            url=qdrant_url,
            api_key=api_key,
        )

        self.embed_model = EmbedModel.get_embed_model()

    def ingest_documents(
        self,
        documents: List[Document],
        user_id:str
    ) -> bool:

        if not documents:
            return True

        texts = [doc.text for doc in documents]

        vectors = self.embed_model.get_text_embedding_batch(
            texts
        )

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": doc.text,
                    "page": doc.metadata.get("page"),
                    "source": doc.metadata.get("source"),
                    "file_path": doc.metadata.get("file_path"),
                    "user_id":user_id
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