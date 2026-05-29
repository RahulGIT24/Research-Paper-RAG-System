from fastapi import APIRouter, UploadFile,status,Depends
from app.core.exceptions import BaseAPIException
from shared_lib.db.session import get_db
from app.core.constants import UPLOAD_DIR
from app.models import Document
from app.middleware.auth import get_current_user
import uuid
from shared_lib.infra.queue import ingest
from sqlalchemy.orm import Session
from shared_lib.pydantic_models.models import JobData
import shutil

router = APIRouter()

allowed_extensions = ["pdf"]

def save_file_to_disk(file:UploadFile) -> str:
        file.filename = str(uuid.uuid4()) + "-" + file.filename
        file_path = UPLOAD_DIR /  file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file,buffer)
        return (file_path,file.filename)

@router.post("/upload")
async def upload(file:UploadFile,current_user=Depends(get_current_user),db:Session = Depends(get_db)):
        original_file_name = file.filename
        ext = original_file_name.split('.')[-1]
        if ext not in allowed_extensions:
                ext_allowed = ", ".join(allowed_extensions)
                message=f"Only {ext_allowed} files are accepted"
                raise BaseAPIException(status_code=status.HTTP_400_BAD_REQUEST,message=message)
        file_path,file_name=save_file_to_disk(file)
        try:
            new_document = Document(file_name=file_name,file_path=str(file_path),original_name=original_file_name,file_ext=ext,uploaded_by=str(current_user['id']))

            db.add(new_document)
            db.commit()
            db.flush()
            new_doc_id = new_document.id

            job_payload:JobData = {
                "id":str(new_doc_id),
                "filepath":new_document.file_path,
                "uploaded_by":str(current_user['id']),
                "status":"uploaded",
                "ext":new_document.file_ext
            }
            await ingest(job_payload)

            return {
                "message": "Document Submitted for processing",
            }
        except BaseAPIException:
            raise BaseAPIException
        except Exception as e:
            db.rollback()
            raise BaseAPIException(message="Internal Server Error",status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

