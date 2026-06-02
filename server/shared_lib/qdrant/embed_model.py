from llama_index.embeddings.fastembed import FastEmbedEmbedding

class EmbedModel:
    @staticmethod
    def get_embed_model(model="BAAI/bge-small-en-v1.5"):
        return FastEmbedEmbedding(
    model_name=model
)