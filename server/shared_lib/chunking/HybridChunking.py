from llama_index.core.schema import Document
from .BaseTextSplitter import BaseSplitter
from .SemanticChunker import SemanticChunker

class HybridChunking:
    @staticmethod
    def hybrid_chunks(full_text: str):
        docs = [Document(text=full_text)]
        base_splitter = BaseSplitter.get_base_splitter()
        semantic_splitter = SemanticChunker.get_semantic_splitter()
        coarse_chunks = base_splitter.get_nodes_from_documents(docs)

        final_chunks = []
        for chunk in coarse_chunks:
            refined = semantic_splitter.get_nodes_from_documents([chunk])
            final_chunks.extend(refined)

        return final_chunks