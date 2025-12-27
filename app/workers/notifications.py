from celery import Task
from sqlalchemy.orm import Session
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import GeneratedContent, SourceContent
from app.config import settings
import structlog

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


@celery_app.task(base=DatabaseTask, bind=True)
def send_approval_notification(self, content_id: int):
    """
    Send email notification for content approval.
    Triggered after content generation completes.
    """
    if not settings.ENABLE_EMAIL_NOTIFICATIONS:
        logger.info("email_notifications_disabled", content_id=content_id)
        return
    
    db = self.db
    
    try:
        content = db.query(GeneratedContent).filter(
            GeneratedContent.id == content_id
        ).first()
        
        if not content:
            raise ValueError(f"Content {content_id} not found")
        
        source = db.query(SourceContent).filter(
            SourceContent.id == content.source_id
        ).first()
        
        logger.info("sending_approval_notification", content_id=content_id)
        
        # Build email content
        subject = f"New {content.platform.value.title()} Content Ready for Review"
        
        # Build review URL (adjust based on your frontend URL)
        review_url = f"{settings.FRONTEND_URL}/approval/{content_id}"
        
        email_body = f"""
        <html>
        <body>
            <h2>Content Ready for Approval</h2>
            
            <p><strong>Video:</strong> {source.title if source else 'Unknown'}</p>
            <p><strong>Platform:</strong> {content.platform.value.title()}</p>
            <p><strong>Generated:</strong> {content.created_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
            
            <h3>Preview:</h3>
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <pre style="white-space: pre-wrap; word-wrap: break-word;">{content.content[:500]}...</pre>
            </div>
            
            <p>
                <a href="{review_url}" style="background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                    Review and Approve
                </a>
            </p>
            
            <p style="color: #666; font-size: 12px;">
                Click the button above to review, edit, and approve this content for publishing.
            </p>
        </body>
        </html>
        """
        
        # Send email based on provider
        if settings.EMAIL_PROVIDER == "resend":
            send_resend_email(subject, email_body)
        elif settings.EMAIL_PROVIDER == "sendgrid":
            send_sendgrid_email(subject, email_body)
        
        logger.info("approval_notification_sent", content_id=content_id)
        
        return {"content_id": content_id, "status": "sent"}
        
    except Exception as e:
        logger.error("notification_failed", content_id=content_id, error=str(e))
        raise


def send_resend_email(subject: str, html_content: str):
    """Send email using Resend"""
    import resend
    
    resend.api_key = settings.RESEND_API_KEY
    
    resend.Emails.send({
        "from": settings.FROM_EMAIL,
        "to": settings.FROM_EMAIL,  # Send to yourself for approval
        "subject": subject,
        "html": html_content
    })


def send_sendgrid_email(subject: str, html_content: str):
    """Send email using SendGrid"""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=settings.FROM_EMAIL,  # Send to yourself
        subject=subject,
        html_content=html_content
    )
    
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)
