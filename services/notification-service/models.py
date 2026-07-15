from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from database import Base, engine

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)       # cross-service ref, no FK
    message = Column(String, nullable=False)
    type = Column(String, nullable=False)           # e.g. booking_confirmation, cancellation, reminder
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

Base.metadata.create_all(bind=engine) #creates table without alembic as teh service is light weight