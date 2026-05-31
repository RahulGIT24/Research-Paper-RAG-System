from llama_index.core.indices.vector_store.base import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from ..core.config import settings

import qdrant_client

client = qdrant_client.QdrantClient(
    url=settings.QDRANT_URL,
    api_key=None
)

vector_store = QdrantVectorStore(client=client, collection_name=settings.QDRANT_COLLECTION)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)