from llama_index.core import Document as LlamaDocument

class DocumentGenerator:
    @staticmethod
    def generate_docs(docs,llama_docs,filepath):
        skip_keywords = {
            "acknowledgements",
            "about the author",
            "license",
            "bibliography",
        }
        llama_docs=[]
        for doc in docs:
            text = doc.page_content.strip()

            if len(text) < 50:
                continue

            text_lower = text.lower()

            text = text.replace(
                "Confidential - Internal Use Only",
                ""
            )

            if text_lower.startswith("contents"):
                continue

            if any(keyword in text_lower for keyword in skip_keywords):
                continue

            llama_docs.append(
                LlamaDocument(
                    text=text,
                    metadata={
                        "page": doc.metadata.get("page"),
                        "source": doc.metadata.get("source"),
                        "file_path": filepath,
                    }
                )
            )
        return llama_docs