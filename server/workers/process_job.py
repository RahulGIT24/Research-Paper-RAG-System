from shared_lib.pydantic_models.models import JobData
from langchain_community.document_loaders import PyMuPDFLoader
from shared_lib.models import DocumentHash
from shared_lib.models.document_hash import DocumentStatus
from sqlalchemy.orm import Session
from llama_index.core import Document as LlamaDocument
import time

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

    def _process_pdf(self, filepath: str,doc_id,user_id,db:Session,filename:str,server_file_name:str,document_hash_id:str):
        print("Started PDF Processing.....")
        rows_updated = db.query(DocumentHash).filter(DocumentHash.id == document_hash_id, DocumentHash.status == 'uploaded').update({"status":"processing"})
        db.commit()

        # the db update is an atomic operation so it will make sure only one row gets updated at a time
        if rows_updated == 0:
            print("No Rows updated here")
            doc_hash = db.query(DocumentHash).filter(
                DocumentHash.id == document_hash_id
            ).first()
            print(str(doc_hash.status))

            if doc_hash.status == DocumentStatus.processing:
                print("Please wait another worker is processing already.....")
                self._wait_and_grant_access(db=db,document_hash_id=document_hash_id,user_id=user_id,server_file_name=server_file_name,doc_id=doc_id,filename=filename,filepath=filepath)
            elif doc_hash.status == DocumentStatus.embedded:
                print("Already Embedded")
                self.qdrant_service.grant_user_access(document_hash_id=document_hash_id,user_id=user_id)

            return

        print("Status Updated")

        try:
            pdf = PyMuPDFLoader(file_path=filepath)
            docs = pdf.load()

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
            self.qdrant_service.ingest_documents(llama_docs,user_id,doc_id,document_hash_id)

            print(f"Ingested Successfully for document hash id {document_hash_id}")

            db.query(DocumentHash).filter(
                    DocumentHash.id == document_hash_id
            ).update({
                    "status": "embedded",
            })
            db.commit()

            return True
        except Exception as e:
            db.query(DocumentHash).filter(
            DocumentHash.id == document_hash_id
            ).update({"status": "uploaded"})
            db.commit()
            print(f"Ingestion failed, rolled back to pending: {e}")
            raise
    

    def _wait_and_grant_access(self,document_hash_id:str,user_id:str,db:Session,filepath,doc_id,filename,server_file_name,interval:int=30,timeout:int=500):
        print("Worker sent to wait")
        elapsed = 0

        while elapsed < timeout:
            print("Elapsed is less than timeout")
            time.sleep(interval)
            elapsed += interval

            db.expire_all()
            doc_hash = db.query(DocumentHash).filter(
                DocumentHash.id == document_hash_id
            ).first()

            if doc_hash.status == DocumentStatus.embedded:
                print("Already Embedded")
                self.qdrant_service.grant_user_access(document_hash_id=document_hash_id,user_id=user_id)
                return
            if doc_hash.status == DocumentStatus.uploaded:
                print("Error while processing previously. Processing again.......")
                self._process_pdf(doc_id=doc_id,db=db,document_hash_id=document_hash_id,filename=filename,filepath=filepath,server_file_name=server_file_name,user_id=user_id)
                return
            print(f"Still processing... waited {elapsed}s")
        print("Error here")
        raise TimeoutError(f"Timed out after {timeout}s waiting for {document_hash_id} to finish processing")

    def _process_docx_file():  
        pass