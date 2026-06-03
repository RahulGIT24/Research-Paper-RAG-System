from shared_lib.pydantic_models.models import JobData
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyMuPDFLoader
from shared_lib.chunking.SemanticChunker import SemanticChunker
from shared_lib.chunking.DocumentGenerator import DocumentGenerator
from shared_lib.models import Document

class ProcessJob:

    def __init__(self,redis_client,splitter,qdrant_service,session_factory):
        self.redis_client=redis_client
        self.splitter = splitter
        self.splitter = SemanticChunker.get_semantic_splitter()
        self.qdrant_service = qdrant_service
        self.session_factory = session_factory

    def process_job(self,data:JobData):
        doc_id = data['id']
        user_id = data['uploaded_by']
        ext = data['ext']
        if ext == 'pdf':
            with self.session_factory() as db:
                self._process_pdf(data['filepath'],doc_id,user_id,db)

    def _process_pdf(self, filepath: str,doc_id,user_id,db):
        pdf = PyMuPDFLoader(file_path=filepath)
        docs = pdf.load()
        db.query(Document).filter(
            Document.id == doc_id
        ).update({
            "status": "processing",
        })
        db.commit()
        print("Status Updated")
        llama_docs = DocumentGenerator.generate_docs(docs,filepath)
        self.qdrant_service.ingest_documents(llama_docs,user_id,doc_id)
        print("Ingested Successfully")
        db.query(Document).filter(
            Document.id == doc_id
        ).update({
            "status": "embedded",
        })
        db.commit()

        # nodes = self.splitter.get_nodes_from_documents(llama_docs)
        # print(f"Generated {len(chunks)} chunks")
    
    def _process_excel():
        pass

    def _process_txt_file():  
        pass