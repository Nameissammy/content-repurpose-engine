import requests
from app.config import settings
import structlog

logger = structlog.get_logger()


class LinkedInPublisher:
    """Publisher for LinkedIn using API"""
    
    def __init__(self):
        self.access_token = settings.LINKEDIN_ACCESS_TOKEN
        self.base_url = "https://api.linkedin.com/v2"
    
    def get_user_urn(self) -> str:
        """Get LinkedIn user URN"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.base_url}/me",
            headers=headers
        )
        response.raise_for_status()
        
        user_id = response.json()["id"]
        return f"urn:li:person:{user_id}"
    
    def publish_post(self, content: str, media_urls: list = None) -> dict:
        """
        Publish a LinkedIn post.
        
        Args:
            content: Post text
            media_urls: Optional list of media URLs
        
        Returns:
            dict with post_id and url
        """
        try:
            logger.info("publishing_linkedin_post")
            
            user_urn = self.get_user_urn()
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Build post payload
            payload = {
                "author": user_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add media if provided (simplified - actual implementation would upload media first)
            if media_urls:
                payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            post_id = response.headers.get("X-RestLi-Id")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}"
            
            logger.info("linkedin_post_published", post_id=post_id, url=post_url)
            
            return {
                "success": True,
                "post_id": post_id,
                "url": post_url
            }
            
        except Exception as e:
            logger.error("linkedin_publish_failed", error=str(e))
            raise
