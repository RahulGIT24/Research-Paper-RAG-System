from sqlalchemy import Column, String, DateTime, ForeignKey,Boolean,Text,Integer
from shared_lib.db.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship,Mapped
import uuid
from datetime import datetime,timezone
from sqlalchemy import Enum
import enum

class DocumentStatus(enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    embedded = "embedded"
    failed = "failed"

class Document(Base):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    file_name = Column(String,nullable=False)
    file_path = Column(String,nullable=False)
    original_name = Column(String,nullable=False)
    created_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    file_ext = Column(String,nullable=False)
    uploaded_by = Column(ForeignKey("users.id"))
    status = Column(
    Enum(DocumentStatus),
        default=DocumentStatus.uploaded
    )
    retry_count = Column(Integer, default=0)
    error_message = Column(Text,default=None,index=True)
    deleted = Column(Boolean,default=False)

    user: Mapped["User"] = relationship("User",back_populates="document")