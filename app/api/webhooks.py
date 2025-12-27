from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SourceContent, ContentStatus
from app.workers.ingestion import ingest_video
import structlog
import re

router = APIRouter()
logger = structlog.get_logger()


class YouTubeWebhookPayload(BaseModel):
    video_url: HttpUrl


class WebhookResponse(BaseModel):
    job_id: str
    video_url: str
    status: str
    message: str


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
        r'youtube\.com/embed/([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError("Invalid YouTube URL")


@router.post("/youtube", response_model=WebhookResponse)
async def youtube_webhook(
    payload: YouTubeWebhookPayload,
    db: Session = Depends(get_db)
):
    """
    Receive YouTube video URL and trigger ingestion workflow.
    
    This endpoint:
    1. Validates the YouTube URL
    2. Checks if video already exists
    3. Creates a new source_content record
    4. Triggers the ingestion Celery task
    """
    try:
        video_url = str(payload.video_url)
        video_id = extract_video_id(video_url)
        
        # Check if video already exists
        existing = db.query(SourceContent).filter(
            SourceContent.video_id == video_id
        ).first()
        
        if existing:
            logger.info("video_already_exists", video_id=video_id)
            return WebhookResponse(
                job_id=str(existing.id),
                video_url=video_url,
                status=existing.status.value,
                message="Video already in system"
            )
        
        # Create new source content record
        source = SourceContent(
            video_url=video_url,
            video_id=video_id,
            status=ContentStatus.PENDING
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        
        # Trigger async ingestion task
        task = ingest_video.delay(source.id)
        
        logger.info(
            "video_ingestion_started",
            video_id=video_id,
            source_id=source.id,
            task_id=task.id
        )
        
        return WebhookResponse(
            job_id=task.id,
            video_url=video_url,
            status="queued",
            message="Video queued for processing"
        )
        
    except ValueError as e:
        logger.error("invalid_youtube_url", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of an ingestion job"""
    from celery.result import AsyncResult
    from app.celery_app import celery_app
    
    result = AsyncResult(job_id, app=celery_app)
    
    return {
        "job_id": job_id,
        "status": result.state,
        "result": result.result if result.ready() else None,
    }
