from llama_index.core.node_parser import SentenceSplitter


class BaseSplitter:
    @staticmethod
    def get_base_splitter():
        return SentenceSplitter(
        chunk_size=430,
        chunk_overlap=75
    )