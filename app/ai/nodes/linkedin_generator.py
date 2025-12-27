from anthropic import Anthropic
from app.config import settings
from app.ai.prompts import LINKEDIN_GENERATOR_PROMPT
import structlog

logger = structlog.get_logger()


def generate_linkedin_post(context_analysis: str, style_guide: str) -> dict:
    """
    Generate LinkedIn post from analyzed content.
    Creates professional, storytelling-style posts optimized for LinkedIn engagement.
    """
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    prompt = LINKEDIN_GENERATOR_PROMPT.format(
        context_analysis=context_analysis,
        style_guide=style_guide
    )
    
    try:
        logger.info("generating_linkedin_post")
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        post_content = response.content[0].text.strip()
        
        # Extract hashtags if they're at the end
        lines = post_content.split('\n')
        hashtags = []
        content_lines = []
        
        for line in lines:
            if line.strip().startswith('#'):
                # This is a hashtag line
                tags = [tag.strip() for tag in line.split() if tag.startswith('#')]
                hashtags.extend(tags)
            else:
                content_lines.append(line)
        
        main_content = '\n'.join(content_lines).strip()
        
        logger.info(
            "linkedin_post_generated",
            character_count=len(main_content),
            hashtag_count=len(hashtags)
        )
        
        # Add hashtags back at the end if they exist
        if hashtags:
            post_with_tags = f"{main_content}\n\n{' '.join(hashtags)}"
        else:
            post_with_tags = main_content
        
        return {
            "platform": "linkedin",
            "content": post_with_tags,
            "character_count": len(main_content),
            "hashtags": hashtags
        }
        
    except Exception as e:
        logger.error("linkedin_generation_failed", error=str(e))
        raise
