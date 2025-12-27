from celery import Task
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import SourceContent, GeneratedContent, Platform, ApprovalStatus
from app.ai.state_machine import run_content_generation
import structlog
import json

logger = structlog.get_logger()


class DatabaseTask(Task):
    """Base task that provides a database session"""
    _db = None
    
    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True, max_retries=2)
def generate_content(self, source_id: int):
    """
    Celery task to generate content for all platforms using LangGraph
    
    Workflow:
    1. Fetch source content with transcript
    2. Run LangGraph state machine
    3. Save generated content to database
    4. Trigger notification worker
    """
    db = self.db
    
    try:
        # Get source content
        source = db.query(SourceContent).filter(SourceContent.id == source_id).first()
        if not source or not source.transcript:
            raise ValueError(f"Source {source_id} not found or has no transcript")
        
        logger.info(
            "content_generation_started",
            source_id=source_id,
            title=source.title
        )
        
        # Prepare metadata
        metadata = {
            "title": source.title,
            "description": source.description,
            **(source.metadata or {})
        }
        
        # Run the AI workflow
        generated = run_content_generation(source.transcript, metadata)
        
        # Save generated content to database
        content_records = []
        
        # Twitter
        if generated.get("twitter"):
            twitter_data = generated["twitter"]
            twitter_record = GeneratedContent(
                source_id=source_id,
                platform=Platform.TWITTER,
                content=twitter_data.get("content", ""),
                content_parts=twitter_data.get("content_parts"),
                approval_status=ApprovalStatus.PENDING_APPROVAL
            )
            db.add(twitter_record)
            content_records.append(("twitter", twitter_record))
        
        # LinkedIn
        if generated.get("linkedin"):
            linkedin_data = generated["linkedin"]
            linkedin_record = GeneratedContent(
                source_id=source_id,
                platform=Platform.LINKEDIN,
                content=linkedin_data.get("content", ""),
                approval_status=ApprovalStatus.PENDING_APPROVAL
            )
            db.add(linkedin_record)
            content_records.append(("linkedin", linkedin_record))
        
        # Newsletter
        if generated.get("newsletter"):
            newsletter_data = generated["newsletter"]
            # Store subject line in metadata
            newsletter_metadata = {"subject_line": newsletter_data.get("subject_line", "")}
            newsletter_record = GeneratedContent(
                source_id=source_id,
                platform=Platform.NEWSLETTER,
                content=newsletter_data.get("content", ""),
                metadata=json.dumps(newsletter_metadata),
                approval_status=ApprovalStatus.PENDING_APPROVAL
            )
            db.add(newsletter_record)
            content_records.append(("newsletter", newsletter_record))
        
        db.commit()
        
        logger.info(
            "content_generation_complete",
            source_id=source_id,
            platforms=len(content_records)
        )
        
        # Trigger notification for approval
        from app.workers.notifications import send_approval_notification
        for platform, record in content_records:
            send_approval_notification.delay(record.id)
        
        return {
            "source_id": source_id,
            "status": "completed",
            "generated_count": len(content_records)
        }
        
    except Exception as e:
        logger.error("content_generation_failed", source_id=source_id, error=str(e))
        raise self.retry(exc=e, countdown=120 * (2 ** self.request.retries))
