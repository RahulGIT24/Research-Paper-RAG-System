from fastapi import APIRouter, UploadFile,status,Depends
from shared_lib.core.exceptions import BaseAPIException
from shared_lib.db.session import get_db
from shared_lib.core.constants import UPLOAD_DIR
from shared_lib.models import Document
from app.middleware.auth import get_current_user
import uuid
from shared_lib.infra.queue import ingest,delete_document
from datetime import datetime,timezone
from sqlalchemy.orm import Session
from shared_lib.pydantic_models.models import JobData
from shared_lib.qdrant.vector_store import QdrantVectorService
import shutil

router = APIRouter()
qdrant = QdrantVectorService()

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

@router.get("/")
def get_documents(
    page: int = 1,
    limit: int = 10,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit

    query = (
        db.query(Document)
        .filter(
            Document.uploaded_by == str(current_user["id"]),
            Document.deleted == False
        )
    )

    total = query.count()

    documents = (
        query.order_by(Document.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "documents": [
            {
                "id": str(doc.id),
                "file_name": doc.original_name,
                "file_ext": doc.file_ext,
                "uploaded_at": doc.created_at,
            }
            for doc in documents
        ]
    }

@router.get("/{document_id}")
def get_document(
    document_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.uploaded_by == str(current_user["id"]),
            Document.deleted == False
        )
        .first()
    )

    if not document:
        raise BaseAPIException(
            status_code=404,
            message="Document not found"
        )

    return {
        "id": str(document.id),
        "file_name": document.original_name,
        "file_ext": document.file_ext,
        "file_path": document.file_path,
        "uploaded_at": document.created_at,
    }


@router.delete("/{document_id}")
async def delete_document_api(
    document_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.uploaded_by == str(current_user["id"]),
            Document.deleted == False
        )
        .first()
    )

    if not document:
        raise BaseAPIException(
            status_code=404,
            message="Document not found"
        )

    # document.deleted = True
    document.deleted_at = datetime.now(timezone.utc)
    db.commit()
    await delete_document(
        {
            "document_id": str(document.id),
            "file_path": document.file_path,
        }
    )

    return {
        "message": "Document deleted successfully"
    }