from shared_lib.db.base import Base
from sqlalchemy import String, Column, UUID,DateTime,ForeignKey
from sqlalchemy.orm import relationship, Mapped
import uuid
from datetime import datetime,timezone

class Messages(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    role = Column(String)
    content = Column(String)
    conversation_id = Column(ForeignKey("conversations.id"))
    created_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))

    conversation: Mapped["Conversation"] = relationship("Conversation",back_populates="messages")