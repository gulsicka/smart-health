from sqlalchemy import Column, Integer, String, DateTime, PrimaryKeyConstraint
from datetime import datetime
from app.database import Base

class AppointmentEvent(Base):
    __tablename__ = "appointment_events"
    id          = Column(Integer, autoincrement=True, nullable=False)
    time        = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type  = Column(String, nullable=False)
    clinic_id   = Column(Integer, nullable=False)
    provider_id = Column(Integer, nullable=False)
    patient_id  = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'time'),
    )


class AIInteractionEvent(Base):
    __tablename__ = "ai_interaction_events"
    id                  = Column(Integer, autoincrement=True, nullable=False)
    time                = Column(DateTime, default=datetime.utcnow, nullable=False)
    event_type          = Column(String, nullable=False) 
    status              = Column(String, nullable=False)
    communication_type  = Column(String, nullable=True)#only set for ai.communication
    user_id             = Column(Integer, nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('id', 'time'),
    )
