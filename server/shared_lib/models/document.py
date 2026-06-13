from sqlalchemy import Column, String, DateTime, ForeignKey,Boolean,Text,Integer
from shared_lib.db.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship,Mapped
import uuid
from datetime import datetime,timezone

class Document(Base):
    __tablename__ = 'documents'

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    file_name = Column(String,nullable=False,index=True)
    file_path = Column(String,nullable=False)
    original_name = Column(String,nullable=False)
    created_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True),default=None)
    file_ext = Column(String,nullable=False)
    document_hash_id = Column(
        ForeignKey("document_hash.id"),
        nullable=False
    )
    uploaded_by = Column(ForeignKey("users.id"))
    retry_count = Column(Integer, default=0)
    error_message = Column(Text,default=None,index=True)
    deleted = Column(Boolean,default=False)

    user: Mapped["User"] = relationship("User",back_populates="document")
    document_hash = relationship(
        "DocumentHash",
        back_populates="documents"
    )