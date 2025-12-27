from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base


class StyleGuide(Base):
    __tablename__ = "style_guide"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    platform = Column(String, nullable=True)  # null means applies to all
    
    # Style rules
    rules = Column(Text, nullable=False)  # Markdown or plain text
    examples = Column(JSON, nullable=True)  # Array of example posts
    
    # Tone and voice
    tone = Column(String, nullable=True)  # e.g., "professional", "casual", "technical"
    voice_description = Column(Text, nullable=True)
    
    # Active flag
    active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
