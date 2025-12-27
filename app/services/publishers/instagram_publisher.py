import requests
from app.config import settings
import structlog

logger = structlog.get_logger()


class InstagramPublisher:
    """Publisher for Instagram using Graph API"""
    
    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.business_account_id = settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def publish_post(self, caption: str, image_url: str = None) -> dict:
        """
        Publish an Instagram post.
        
        Note: Instagram requires a 2-step process:
        1. Create media container
        2. Publish container
        
        Args:
            caption: Post caption
            image_url: URL to publicly accessible image
        
        Returns:
            dict with post_id and url
        """
        try:
            logger.info("publishing_instagram_post")
            
            # Step 1: Create media container
            container_params = {
                "caption": caption,
                "access_token": self.access_token
            }
            
            if image_url:
                container_params["image_url"] = image_url
            else:
                # For text-only (not typical for Instagram), you'd need a default image
                logger.warning("instagram_post_without_image")
            
            container_response = requests.post(
                f"{self.base_url}/{self.business_account_id}/media",
                params=container_params
            )
            container_response.raise_for_status()
            container_id = container_response.json()["id"]
            
            logger.info("instagram_container_created", container_id=container_id)
            
            # Step 2: Publish the container
            publish_params = {
                "creation_id": container_id,
                "access_token": self.access_token
            }
            
            publish_response = requests.post(
                f"{self.base_url}/{self.business_account_id}/media_publish",
                params=publish_params
            )
            publish_response.raise_for_status()
            post_id = publish_response.json()["id"]
            
            post_url = f"https://www.instagram.com/p/{post_id}"
            
            logger.info("instagram_post_published", post_id=post_id, url=post_url)
            
            return {
                "success": True,
                "post_id": post_id,
                "url": post_url
            }
            
        except Exception as e:
            logger.error("instagram_publish_failed", error=str(e))
            raise
