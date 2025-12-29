from openai import OpenAI
from app.config import settings
from app.ai.prompts import CONTEXT_ANALYZER_PROMPT
import structlog

logger = structlog.get_logger()


def analyze_context(transcript: str, video_metadata: dict = None) -> dict:
    """
    Analyze video transcript to extract key insights and context.
    This is the first node in the LangGraph workflow.
    """
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Build the analysis prompt
    prompt = CONTEXT_ANALYZER_PROMPT.format(transcript=transcript)
    
    # Add metadata context if available
    if video_metadata:
        title = video_metadata.get('title', '')
        description = video_metadata.get('description', '')
        prompt = f"Video Title: {title}\n\nDescription: {description}\n\n{prompt}"
    
    try:
        logger.info("analyzing_context", transcript_length=len(transcript))
        
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            temperature=0.3,  # Lower temperature for analytical task
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        analysis = response.choices[0].message.content
        
        logger.info("context_analysis_complete", analysis_length=len(analysis))
        
        return {
            "analysis": analysis,
            "transcript": transcript,
            "metadata": video_metadata
        }
        
    except Exception as e:
        logger.error("context_analysis_failed", error=str(e))
        raise
