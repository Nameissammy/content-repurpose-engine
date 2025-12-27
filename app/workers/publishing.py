from celery import Task
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import GeneratedContent, ApprovalStatus, Platform
from app.services.publishers.twitter_publisher import TwitterPublisher
from app.services.publishers.linkedin_publisher import LinkedInPublisher
from app.services.publishers.instagram_publisher import InstagramPublisher
from app.services.publishers.newsletter_publisher import NewsletterPublisher
from datetime import datetime
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


@celery_app.task(base=DatabaseTask, bind=True, max_retries=3)
def publish_content(self, content_id: int):
    """
    Celery task to publish approved content to social media platforms.
    
    Workflow:
    1. Fetch approved content
    2. Route to platform-specific publisher
    3. Update database with published URL
    4. Handle errors with retry logic
    """
    db = self.db
    
    try:
        # Get content
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        
        if not content:
            raise ValueError(f"Content {content_id} not found")
        
        if content.approval_status != ApprovalStatus.APPROVED:
            raise ValueError(f"Content {content_id} not approved for publishing")
        
        logger.info(
            "publishing_content",
            content_id=content_id,
            platform=content.platform.value
        )
        
        # Route to appropriate publisher
        result = None
        
        if content.platform == Platform.TWITTER:
            result = _publish_twitter(content)
        elif content.platform == Platform.LINKEDIN:
            result = _publish_linkedin(content)
        elif content.platform == Platform.INSTAGRAM:
            result = _publish_instagram(content)
        elif content.platform == Platform.NEWSLETTER:
            result = _publish_newsletter(content)
        else:
            raise ValueError(f"Unknown platform: {content.platform}")
        
        # Update database
        content.approval_status = ApprovalStatus.PUBLISHED
        content.published_url = result.get("url")
        content.published_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            "content_published",
            content_id=content_id,
            platform=content.platform.value,
            url=result.get("url")
        )
        
        return {
            "content_id": content_id,
            "platform": content.platform.value,
            "status": "published",
            "url": result.get("url")
        }
        
    except Exception as e:
        logger.error(
            "publishing_failed",
            content_id=content_id,
            error=str(e),
            retry_count=self.request.retries
        )
        
        # Update error in database
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        if content:
            content.approval_status = ApprovalStatus.FAILED
            content.error_message = str(e)
            content.retry_count = self.request.retries
            db.commit()
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


def _publish_twitter(content: GeneratedContent) -> dict:
    """Publish to Twitter"""
    publisher = TwitterPublisher()
    
    # Parse tweets from content_parts
    if content.content_parts:
        tweets = json.loads(content.content_parts)
    else:
        # Fallback: split content by newlines
        tweets = [t.strip() for t in content.content.split('\n\n') if t.strip()]
    
    return publisher.publish_thread(tweets)


def _publish_linkedin(content: GeneratedContent) -> dict:
    """Publish to LinkedIn"""
    publisher = LinkedInPublisher()
    
    # Get media URLs if any
    media_urls = None
    if content.media_urls:
        media_urls = json.loads(content.media_urls)
    
    return publisher.publish_post(content.content, media_urls)


def _publish_instagram(content: GeneratedContent) -> dict:
    """Publish to Instagram"""
    publisher = InstagramPublisher()
    
    # Instagram requires an image
    image_url = None
    if content.media_urls:
        media_urls = json.loads(content.media_urls)
        image_url = media_urls[0] if media_urls else None
    
    if not image_url:
        raise ValueError("Instagram posts require an image URL")
    
    return publisher.publish_post(content.content, image_url)


def _publish_newsletter(content: GeneratedContent) -> dict:
    """Publish newsletter"""
    publisher = NewsletterPublisher()
    
    # Extract subject line from metadata
    subject = "Newsletter"
    if content.metadata:
        metadata = json.loads(content.metadata)
        subject = metadata.get("subject_line", subject)
    
    return publisher.publish_newsletter(subject, content.content)
