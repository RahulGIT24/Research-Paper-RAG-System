from sqlalchemy import Column, DateTime, String, UUID,ForeignKey
import uuid
from sqlalchemy.orm import Mapped,relationship
from shared_lib.db.base import Base
from datetime import datetime,timezone

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    name = Column(String,nullable=False)
    user_id = Column(ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))
    user: Mapped["User"] = relationship("User",back_populates="conversation")
    messages:Mapped["Messages"] = relationship(back_populates="conversation")