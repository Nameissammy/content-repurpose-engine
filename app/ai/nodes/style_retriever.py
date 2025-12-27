from sqlalchemy.orm import Session
from app.models import StyleGuide
from app.ai.prompts import STYLE_GUIDE_TEMPLATE
import structlog

logger = structlog.get_logger()


def retrieve_style_guide(db: Session, platform: str = None) -> dict:
    """
    Retrieve style guide from database.
    This node fetches the active style guidelines for content generation.
    """
    try:
        # Query for active style guides
        query = db.query(StyleGuide).filter(StyleGuide.active == True)
        
        # Filter by platform if specified, otherwise get general guide
        if platform:
            style_guide = query.filter(StyleGuide.platform == platform).first()
            if not style_guide:
                # Fall back to general guide
                style_guide = query.filter(StyleGuide.platform == None).first()
        else:
            style_guide = query.filter(StyleGuide.platform == None).first()
        
        if not style_guide:
            logger.warning("no_style_guide_found", platform=platform)
            return {
                "style_rules": "Create engaging, authentic content.",
                "tone": "conversational",
                "voice_description": "Knowledgeable but approachable",
                "examples": []
            }
        
        logger.info("style_guide_retrieved", name=style_guide.name, platform=platform)
        
        # Format the style guide
        formatted_guide = STYLE_GUIDE_TEMPLATE.format(
            style_rules=style_guide.rules,
            tone=style_guide.tone or "conversational",
            voice_description=style_guide.voice_description or "Authentic and engaging",
            examples="\n".join(style_guide.examples or [])
        )
        
        return {
            "style_guide": formatted_guide,
            "style_rules": style_guide.rules,
            "tone": style_guide.tone,
            "voice_description": style_guide.voice_description,
            "examples": style_guide.examples or []
        }
        
    except Exception as e:
        logger.error("style_guide_retrieval_failed", error=str(e))
        # Return default style guide on error
        return {
            "style_rules": "Create engaging, authentic content.",
            "tone": "conversational",
            "voice_description": "Knowledgeable but approachable",
            "examples": []
        }
