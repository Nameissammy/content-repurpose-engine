from openai import OpenAI
from app.config import settings
from app.ai.prompts import NEWSLETTER_GENERATOR_PROMPT
import structlog

logger = structlog.get_logger()


def generate_newsletter(context_analysis: str, style_guide: str) -> dict:
    """
    Generate newsletter/email content from analyzed content.
    Creates educational, well-structured email content with subject line.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    prompt = NEWSLETTER_GENERATOR_PROMPT.format(
        context_analysis=context_analysis,
        style_guide=style_guide
    )
    
    try:
        logger.info("generating_newsletter")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=3500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        newsletter_content = response.choices[0].message.content.strip()
        
        # Extract subject line
        subject_line = ""
        body_content = newsletter_content
        
        if newsletter_content.startswith("Subject"):
            lines = newsletter_content.split('\n', 2)
            if len(lines) >= 2:
                subject_line = lines[0].replace("Subject Line:", "").replace("Subject:", "").strip()
                # Skip the subject line and any empty line
                body_content = lines[2] if len(lines) > 2 else lines[1]
        
        logger.info(
            "newsletter_generated",
            subject=subject_line,
            word_count=len(body_content.split())
        )
        
        return {
            "platform": "newsletter",
            "content": body_content,
            "subject_line": subject_line,
            "word_count": len(body_content.split())
        }
        
    except Exception as e:
        logger.error("newsletter_generation_failed", error=str(e))
        raise
