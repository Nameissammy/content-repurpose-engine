from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class Platform(str, enum.Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    NEWSLETTER = "newsletter"


class ApprovalStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class GeneratedContent(Base):
    __tablename__ = "generated_content"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("source_content.id"), nullable=False, index=True)
    
    # Platform and content
    platform = Column(SQLEnum(Platform), nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # For Twitter threads or multi-part content
    content_parts = Column(Text, nullable=True)  # JSON array
    
    # Media attachments
    media_urls = Column(Text, nullable=True)  # JSON array
    
    # Approval workflow
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING_APPROVAL, nullable=False)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Publishing
    published_url = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
