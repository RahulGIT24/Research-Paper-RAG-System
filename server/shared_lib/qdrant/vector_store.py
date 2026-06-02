from typing import List

import qdrant_client
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.vector_stores.qdrant import QdrantVectorStore
from .embed_model import EmbedModel
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

class QdrantVectorService:
    def __init__(
        self,
        qdrant_url: str,
        collection_name: str,
        api_key: str | None = None,
    ):
        self.collection_name = collection_name

        self.client = qdrant_client.QdrantClient(
            url=qdrant_url,
            api_key=api_key,
        )

        self.embed_model = EmbedModel.get_embed_model()

        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
        )

    def ingest_documents(
        self,
        documents: List[Document],
    ) -> VectorStoreIndex:
        """
        Creates embeddings and stores them in Qdrant.
        """
        print("Ingesting Documents.......")
        points = []

        for doc in documents:
            vector = self.embed_model.get_text_embedding(doc.text)

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": doc.text,
                        "page": doc.metadata.get("page"),
                        "source": doc.metadata.get("source")
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return True

    def get_index(self) -> VectorStoreIndex:
        """
        Connect to an existing collection.
        """

        return VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store
        )

    def query(
        self,
        query_text: str,
        top_k: int = 5,
    ) -> str:
        """
        Query the collection.
        """

        index = self.get_index()

        query_engine = index.as_query_engine(
            similarity_top_k=top_k
        )

        response = query_engine.query(query_text)

        return str(response)