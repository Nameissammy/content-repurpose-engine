from celery import Task
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import SourceContent, ContentStatus
from app.services.youtube_downloader import YouTubeDownloader
from app.services.transcription import TranscriptionService
import structlog
from datetime import datetime

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


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def ingest_video(self, source_id: int):
    """
    Celery task to ingest a YouTube video:
    1. Fetch video metadata
    2. Get transcript from YouTube
    3. Store in database
    4. Trigger content generation
    """
    db = self.db
    downloader = YouTubeDownloader()
    transcriber = TranscriptionService()
    
    try:
        # Get source content record
        source = db.query(SourceContent).filter(SourceContent.id == source_id).first()
        if not source:
            raise ValueError(f"Source content {source_id} not found")
        
        # Update status to processing
        source.status = ContentStatus.PROCESSING
        db.commit()
        
        logger.info("ingestion_started", source_id=source_id, video_url=source.video_url)
        
        # Step 1: Get video metadata (without downloading audio)
        metadata = downloader.get_metadata(source.video_url, source.video_id)
        
        # Step 2: Fetch transcript from YouTube
        transcript_data = transcriber.get_transcript(source.video_id)
        
        # Step 3: Update database with all information
        source.title = metadata.get('title')
        source.description = metadata.get('description')
        source.duration = metadata.get('duration')
        source.transcript = transcript_data['text']
        source.metadata = {
            'uploader': metadata.get('uploader'),
            'upload_date': metadata.get('upload_date'),
            'view_count': metadata.get('view_count'),
            'like_count': metadata.get('like_count'),
            'language': transcript_data.get('language'),
            'segments': transcript_data.get('segments', [])
        }
        source.status = ContentStatus.COMPLETED
        source.processed_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            "ingestion_completed",
            source_id=source_id,
            title=source.title,
            transcript_length=len(source.transcript)
        )
        
        # Step 4: Trigger content generation workflow
        from app.workers.content_generation import generate_content
        generate_content.delay(source_id)
        
        return {
            "source_id": source_id,
            "status": "completed",
            "title": source.title
        }
        
    except Exception as e:
        logger.error("ingestion_failed", source_id=source_id, error=str(e))
        
        # Update status to failed
        source = db.query(SourceContent).filter(SourceContent.id == source_id).first()
        if source:
            source.status = ContentStatus.FAILED
            source.error_message = str(e)
            db.commit()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
