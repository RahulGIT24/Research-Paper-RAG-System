import os
from llama_index.embeddings.fastembed import FastEmbedEmbedding

FASTEMBED_CACHE_DIR = os.path.join(
    os.path.expanduser("~"), ".cache", "huggingface", "fastembed"
)

class EmbedModel:
    @staticmethod
    def get_embed_model(model="BAAI/bge-small-en-v1.5"):
        return FastEmbedEmbedding(
            model_name=model,
            cache_dir=FASTEMBED_CACHE_DIR
        )