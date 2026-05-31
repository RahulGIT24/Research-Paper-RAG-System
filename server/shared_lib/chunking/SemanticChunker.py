from llama_index.core.node_parser import (
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.fastembed import FastEmbedEmbedding

EMBED_MODEL = FastEmbedEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)
class SemanticChunker:
    @staticmethod
    def get_semantic_splitter():
        return SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=80,
            embed_model=EMBED_MODEL
        )