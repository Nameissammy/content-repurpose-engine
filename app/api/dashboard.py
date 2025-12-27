from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import SourceContent, GeneratedContent, ContentStatus, ApprovalStatus
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Total videos processed
        total_videos = db.query(func.count(SourceContent.id)).scalar()
        
        # Videos by status
        pending_videos = db.query(func.count(SourceContent.id)).filter(
            SourceContent.status == ContentStatus.PENDING
        ).scalar()
        
        processing_videos = db.query(func.count(SourceContent.id)).filter(
            SourceContent.status == ContentStatus.PROCESSING
        ).scalar()
        
        completed_videos = db.query(func.count(SourceContent.id)).filter(
            SourceContent.status == ContentStatus.COMPLETED
        ).scalar()
        
        # Generated content stats
        total_content = db.query(func.count(GeneratedContent.id)).scalar()
        
        pending_approval = db.query(func.count(GeneratedContent.id)).filter(
            GeneratedContent.approval_status == ApprovalStatus.PENDING_APPROVAL
        ).scalar()
        
        approved_content = db.query(func.count(GeneratedContent.id)).filter(
            GeneratedContent.approval_status == ApprovalStatus.APPROVED
        ).scalar()
        
        published_content = db.query(func.count(GeneratedContent.id)).filter(
            GeneratedContent.approval_status == ApprovalStatus.PUBLISHED
        ).scalar()
        
        return {
            "videos": {
                "total": total_videos,
                "pending": pending_videos,
                "processing": processing_videos,
                "completed": completed_videos
            },
            "content": {
                "total": total_content,
                "pending_approval": pending_approval,
                "approved": approved_content,
                "published": published_content
            }
        }
        
    except Exception as e:
        logger.error("dashboard_stats_failed", error=str(e))
        return {"error": str(e)}


@router.get("/recent")
async def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent activity"""
    try:
        recent_videos = db.query(SourceContent).order_by(
            SourceContent.created_at.desc()
        ).limit(limit).all()
        
        recent_content = db.query(GeneratedContent).order_by(
            GeneratedContent.created_at.desc()
        ).limit(limit).all()
        
        return {
            "recent_videos": [
                {
                    "id": v.id,
                    "title": v.title,
                    "status": v.status.value,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in recent_videos
            ],
            "recent_content": [
                {
                    "id": c.id,
                    "platform": c.platform.value,
                    "approval_status": c.approval_status.value,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in recent_content
            ]
        }
        
    except Exception as e:
        logger.error("recent_activity_failed", error=str(e))
        return {"error": str(e)}
