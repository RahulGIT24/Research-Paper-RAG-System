from sqlalchemy import Column, String, DateTime
from shared_lib.db.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from sqlalchemy import Enum
from datetime import datetime,timezone

class DocumentStatus(enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    embedded = "embedded"
    failed = "failed"


class DocumentHash(Base):
    __tablename__ = "document_hash"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    hash_value = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )
    status = Column(
    Enum(DocumentStatus),
        default=DocumentStatus.uploaded
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc)
    )

    documents = relationship(
        "Document",
        back_populates="document_hash"
    )