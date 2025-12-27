from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import GeneratedContent, SourceContent, ApprovalStatus, Platform
from datetime import datetime
import structlog

router = APIRouter()
logger = structlog.get_logger()


class ContentResponse(BaseModel):
    id: int
    source_id: int
    platform: str
    content: str
    content_parts: Optional[str] = None
    approval_status: str
    created_at: datetime
    
    # Source video info
    video_title: Optional[str] = None
    video_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class ContentUpdateRequest(BaseModel):
    content: str
    content_parts: Optional[str] = None


class ApprovalRequest(BaseModel):
    approved_by: str = "admin"


@router.get("/pending", response_model=List[ContentResponse])
async def get_pending_content(db: Session = Depends(get_db)):
    """Get all content pending approval"""
    try:
        content_items = db.query(GeneratedContent).join(SourceContent).filter(
            GeneratedContent.approval_status == ApprovalStatus.PENDING_APPROVAL
        ).all()
        
        response = []
        for item in content_items:
            response.append(ContentResponse(
                id=item.id,
                source_id=item.source_id,
                platform=item.platform.value,
                content=item.content,
                content_parts=item.content_parts,
                approval_status=item.approval_status.value,
                created_at=item.created_at,
                video_title=item.source.title if hasattr(item, 'source') else None,
                video_url=item.source.video_url if hasattr(item, 'source') else None,
            ))
        
        logger.info("pending_content_retrieved", count=len(response))
        return response
        
    except Exception as e:
        logger.error("get_pending_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: Session = Depends(get_db)):
    """Get specific content by ID"""
    try:
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        source = db.query(SourceContent).filter(
            SourceContent.id == content.source_id
        ).first()
        
        return ContentResponse(
            id=content.id,
            source_id=content.source_id,
            platform=content.platform.value,
            content=content.content,
            content_parts=content.content_parts,
            approval_status=content.approval_status.value,
            created_at=content.created_at,
            video_title=source.title if source else None,
            video_url=source.video_url if source else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_content_failed", content_id=content_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    update: ContentUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update/edit generated content"""
    try:
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Update content
        content.content = update.content
        if update.content_parts:
            content.content_parts = update.content_parts
        
        db.commit()
        db.refresh(content)
        
        logger.info("content_updated", content_id=content_id)
        
        source = db.query(SourceContent).filter(
            SourceContent.id == content.source_id
        ).first()
        
        return ContentResponse(
            id=content.id,
            source_id=content.source_id,
            platform=content.platform.value,
            content=content.content,
            content_parts=content.content_parts,
            approval_status=content.approval_status.value,
            created_at=content.created_at,
            video_title=source.title if source else None,
            video_url=source.video_url if source else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_content_failed", content_id=content_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{content_id}/approve")
async def approve_content(
    content_id: int,
    approval: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """Approve content and trigger publishing"""
    try:
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Update approval status
        content.approval_status = ApprovalStatus.APPROVED
        content.approved_by = approval.approved_by
        content.approved_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            "content_approved",
            content_id=content_id,
            platform=content.platform.value,
            approved_by=approval.approved_by
        )
        
        # Trigger publishing worker
        from app.workers.publishing import publish_content
        publish_content.delay(content_id)
        
        return {
            "status": "approved",
            "content_id": content_id,
            "message": "Content approved and queued for publishing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("approve_content_failed", content_id=content_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{content_id}/reject")
async def reject_content(content_id: int, db: Session = Depends(get_db)):
    """Reject generated content"""
    try:
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        content.approval_status = ApprovalStatus.REJECTED
        db.commit()
        
        logger.info("content_rejected", content_id=content_id)
        
        return {
            "status": "rejected",
            "content_id": content_id,
            "message": "Content rejected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("reject_content_failed", content_id=content_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
