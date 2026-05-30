from shared_lib.pydantic_models.models import JobData
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyMuPDFLoader
from shared_lib.chunking.HybridChunking import HybridChunking

class ProcessJob:

    def __init__(self,db:Session,redis_client,splitter):
        self.db=db
        self.redis_client=redis_client
        self.splitter = splitter

    async def process_job(self,data:JobData):
        ext = data['ext']
        if ext == 'pdf':
            await self._process_pdf(data['filepath'])
    
    async def _process_pdf(self,filepath:str):
        pdf = PyMuPDFLoader(file_path=filepath)
        docs = pdf.load()
        full_text = "\n".join(doc.page_content for doc in docs)
        chunks = HybridChunking.hybrid_chunks(full_text=full_text)
        print(chunks)

    
    async def _process_excel():
        pass

    async def _process_txt_file():  
        pass