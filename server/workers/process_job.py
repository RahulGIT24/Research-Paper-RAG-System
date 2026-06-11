from shared_lib.pydantic_models.models import JobData
from langchain_community.document_loaders import PyMuPDFLoader
from shared_lib.models import DocumentHash
from llama_index.core import Document as LlamaDocument

class ProcessJob:

    def __init__(self,redis_client,splitter,qdrant_service,session_factory):
        self.redis_client=redis_client
        self.splitter = splitter
        self.qdrant_service = qdrant_service
        self.session_factory = session_factory

    def process_job(self,data:JobData):
        doc_id = data['id']
        user_id = data['uploaded_by']
        ext = data['ext']
        server_file_name = data['server_file_name']
        document_hash_id = data['hash_id']
        filename = data['filename']
        if ext == 'pdf':
            with self.session_factory() as db:
                self._process_pdf(data['filepath'],doc_id,user_id,db,filename,server_file_name,document_hash_id)

    def _process_pdf(self, filepath: str,doc_id,user_id,db,filename:str,server_file_name:str,document_hash_id:str):
        pdf = PyMuPDFLoader(file_path=filepath)
        docs = pdf.load()
        db.query(DocumentHash).filter(
            DocumentHash.id == document_hash_id
        ).update({
            "status": "processing",
        })
        db.commit()
        print("Status Updated")

        #convert to llama index docs
        llama_docs = [
            LlamaDocument(text=d.page_content, metadata={"page":i})
            for i,d in enumerate(docs)
        ]

        nodes = self.splitter.get_nodes_from_documents(llama_docs)

        llama_docs = [
            {
                "text":node.get_content(),
                "metadata":{
                    "page":node.metadata.get("page"),
                    "server_file_name":server_file_name,
                    "source":"upload",
                    "file_name":filename
                }
            }
            for node in nodes
        ]

        self.qdrant_service.ingest_documents(llama_docs,user_id,doc_id)
        print("Ingested Successfully")

        db.query(DocumentHash).filter(
            DocumentHash.id == document_hash_id
        ).update({
            "status": "embedded",
        })
        db.commit()

    def _process_docx_file():  
        pass