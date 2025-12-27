from anthropic import Anthropic
from app.config import settings
from app.ai.prompts import TWITTER_GENERATOR_PROMPT
import structlog
import json

logger = structlog.get_logger()


def generate_twitter_thread(context_analysis: str, style_guide: str) -> dict:
    """
    Generate Twitter/X thread from analyzed content.
    Uses Claude 3.5 Sonnet to create engaging, viral-style tweets.
    """
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    prompt = TWITTER_GENERATOR_PROMPT.format(
        context_analysis=context_analysis,
        style_guide=style_guide
    )
    
    try:
        logger.info("generating_twitter_thread")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,
            temperature=0.7,  # Higher temperature for creative content
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        thread_text = response.content[0].text
        
        # Parse tweets from the response
        tweets = [
            tweet.strip()
            for tweet in thread_text.split("---TWEET---")
            if tweet.strip()
        ]
        
        # Validate tweet length
        validated_tweets = []
        for i, tweet in enumerate(tweets):
            if len(tweet) > 280:
                logger.warning("tweet_too_long", tweet_number=i+1, length=len(tweet))
                # Try to truncate intelligently
                tweet = tweet[:277] + "..."
            validated_tweets.append(tweet)
        
        logger.info("twitter_thread_generated", tweet_count=len(validated_tweets))
        
        return {
            "platform": "twitter",
            "content": "\n\n".join(validated_tweets),  # Full thread as single string
            "content_parts": json.dumps(validated_tweets),  # Individual tweets as JSON
            "tweet_count": len(validated_tweets)
        }
        
    except Exception as e:
        logger.error("twitter_generation_failed", error=str(e))
        raise
