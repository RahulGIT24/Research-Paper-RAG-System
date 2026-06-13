from sqlalchemy import Column, Boolean, String, DateTime
from shared_lib.db.base import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship,Mapped
import uuid
from datetime import datetime,timezone

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    name = Column(String,nullable=False)
    email = Column(String, index=True, unique=True,nullable=False)
    password_hash = Column(String,nullable=False)
    is_active = Column(Boolean, default=True)
    verification_token = Column(String, default=None)
    forgot_password_token = Column(String, default=None)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True),default=datetime.now(timezone.utc))

    document:Mapped["Document"] = relationship(back_populates="user")