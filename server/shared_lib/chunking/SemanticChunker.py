from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.fastembed import FastEmbedEmbedding

class SemanticChunker:
    @staticmethod
    def get_semantic_splitter(model:str="BAAI/bge-small-en-v1.5"):
        embed_model = FastEmbedEmbedding(model_name=model)

        return SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=80,
            embed_model=embed_model
        )