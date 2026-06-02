from shared_lib.pydantic_models.models import JobData
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyMuPDFLoader
from shared_lib.chunking.SemanticChunker import SemanticChunker
from shared_lib.chunking.DocumentGenerator import DocumentGenerator

class ProcessJob:

    def __init__(self,db:Session,redis_client,splitter,qdrant_service):
        self.db=db
        self.redis_client=redis_client
        self.splitter = splitter
        self.splitter = SemanticChunker.get_semantic_splitter()
        self.qdrant_service = qdrant_service

    async def process_job(self,data:JobData):
        ext = data['ext']
        if ext == 'pdf':
            await self._process_pdf(data['filepath'])

    async def _process_pdf(self, filepath: str):
        pdf = PyMuPDFLoader(file_path=filepath)
        docs = pdf.load()
        llama_docs = DocumentGenerator.generate_docs(docs,filepath)
        self.qdrant_service.ingest_documents(llama_docs)
        print("Ingested Successfully")

        # nodes = self.splitter.get_nodes_from_documents(llama_docs)
        # print(f"Generated {len(chunks)} chunks")
    
    async def _process_excel():
        pass

    async def _process_txt_file():  
        pass