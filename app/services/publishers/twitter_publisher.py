import tweepy
from app.config import settings
import structlog

logger = structlog.get_logger()


class TwitterPublisher:
    """Publisher for Twitter/X using API v2"""
    
    def __init__(self):
        # Twitter API v2 client
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_SECRET,
            wait_on_rate_limit=True
        )
    
    def publish_thread(self, tweets: list) -> dict:
        """
        Publish a Twitter thread.
        
        Args:
            tweets: List of tweet texts
        
        Returns:
            dict with thread_id and tweet_ids
        """
        try:
            logger.info("publishing_twitter_thread", tweet_count=len(tweets))
            
            tweet_ids = []
            previous_tweet_id = None
            
            for i, tweet_text in enumerate(tweets):
                # Post tweet, reply to previous if it's a thread
                if previous_tweet_id:
                    response = self.client.create_tweet(
                        text=tweet_text,
                        in_reply_to_tweet_id=previous_tweet_id
                    )
                else:
                    response = self.client.create_tweet(text=tweet_text)
                
                tweet_id = response.data['id']
                tweet_ids.append(tweet_id)
                previous_tweet_id = tweet_id
                
                logger.info(
                    "tweet_published",
                    tweet_number=i+1,
                    tweet_id=tweet_id
                )
            
            # Build thread URL (first tweet)
            thread_url = f"https://twitter.com/user/status/{tweet_ids[0]}"
            
            logger.info(
                "twitter_thread_complete",
                thread_url=thread_url,
                tweet_count=len(tweet_ids)
            )
            
            return {
                "success": True,
                "thread_id": tweet_ids[0],
                "tweet_ids": tweet_ids,
                "url": thread_url
            }
            
        except Exception as e:
            logger.error("twitter_publish_failed", error=str(e))
            raise
