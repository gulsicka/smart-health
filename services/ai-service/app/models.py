from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from pgvector.sqlalchemy import Vector
from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id         = Column(Integer, primary_key=True, index=True)
    source     = Column(String, nullable=False, index=True)
    content    = Column(Text, nullable=False)
    embedding  = Column(Vector(384), nullable=False)  # all-MiniLM-L6-v2 outputs 384 dimensions
    file_hash  = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
