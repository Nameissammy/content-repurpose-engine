from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum
from app.database import Base


class ContentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SourceContent(Base):
    __tablename__ = "source_content"
    
    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String, unique=True, nullable=False, index=True)
    video_id = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    
    # Audio and transcript
    audio_path = Column(String, nullable=True)
    transcript = Column(Text, nullable=True)
    
    # Embeddings for semantic search
    embedding = Column(Vector(1536), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(ContentStatus), default=ContentStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
