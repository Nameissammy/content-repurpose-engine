from app.config import settings
import structlog

logger = structlog.get_logger()


class NewsletterPublisher:
    """Publisher for email newsletters"""
    
    def __init__(self):
        self.provider = settings.EMAIL_PROVIDER
    
    def publish_newsletter(self, subject: str, html_content: str, recipients: list = None) -> dict:
        """
        Send newsletter email.
        
        Args:
            subject: Email subject line
            html_content: HTML email body
            recipients: List of recipient emails (default: send to self)
        
        Returns:
            dict with success status and email_id
        """
        try:
            logger.info("publishing_newsletter", provider=self.provider)
            
            if recipients is None:
                # Default to sending to yourself
                recipients = [settings.FROM_EMAIL]
            
            if self.provider == "resend":
                result = self._send_resend(subject, html_content, recipients)
            elif self.provider == "sendgrid":
                result = self._send_sendgrid(subject, html_content, recipients)
            else:
                raise ValueError(f"Unknown email provider: {self.provider}")
            
            logger.info("newsletter_published", recipient_count=len(recipients))
            
            return result
            
        except Exception as e:
            logger.error("newsletter_publish_failed", error=str(e))
            raise
    
    def _send_resend(self, subject: str, html_content: str, recipients: list) -> dict:
        """Send via Resend"""
        import resend
        
        resend.api_key = settings.RESEND_API_KEY
        
        email_data = {
            "from": settings.FROM_EMAIL,
            "to": recipients,
            "subject": subject,
            "html": html_content
        }
        
        response = resend.Emails.send(email_data)
        
        return {
            "success": True,
            "email_id": response.get("id"),
            "provider": "resend"
        }
    
    def _send_sendgrid(self, subject: str, html_content: str, recipients: list) -> dict:
        """Send via SendGrid"""
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=settings.FROM_EMAIL,
            to_emails=recipients,
            subject=subject,
            html_content=html_content
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        return {
            "success": True,
            "email_id": response.headers.get("X-Message-Id"),
            "provider": "sendgrid",
            "status_code": response.status_code
        }
