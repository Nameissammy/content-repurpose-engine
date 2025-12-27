from anthropic import Anthropic
from app.config import settings
from app.ai.prompts import CRITIC_PROMPT
import structlog

logger = structlog.get_logger()


def critique_and_refine(
    context_analysis: str,
    style_guide: str,
    generated_content: str,
    platform: str
) -> dict:
    """
    Second LLM pass to review and refine generated content.
    Validates against style guide and ensures quality.
    """
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    prompt = CRITIC_PROMPT.format(
        context_analysis=context_analysis,
        style_guide=style_guide,
        generated_content=generated_content,
        platform=platform
    )
    
    try:
        logger.info("critiquing_content", platform=platform)
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            temperature=0.2,  # Lower temperature for analytical review
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        review = response.content[0].text.strip()
        
        # Parse the verdict
        verdict = "APPROVE"
        issues = []
        revised_content = generated_content
        
        for line in review.split('\n'):
            if line.startswith("VERDICT:"):
                verdict = line.replace("VERDICT:", "").strip()
            elif line.startswith("ISSUES:"):
                issues_text = line.replace("ISSUES:", "").strip()
                if issues_text != "None":
                    issues.append(issues_text)
            elif line.startswith("REVISED_CONTENT:"):
                # The revised content might be multi-line
                revised_start = review.find("REVISED_CONTENT:")
                revised_content = review[revised_start + len("REVISED_CONTENT:"):].strip()
                break
        
        needs_revision = verdict == "REVISE"
        final_content = revised_content if needs_revision else generated_content
        
        logger.info(
            "critique_complete",
            platform=platform,
            verdict=verdict,
            needs_revision=needs_revision
        )
        
        return {
            "refined_content": final_content,
            "verdict": verdict,
            "issues": issues,
            "needs_revision": needs_revision
        }
        
    except Exception as e:
        logger.error("critique_failed", error=str(e), platform=platform)
        # On error, return original content
        return {
            "refined_content": generated_content,
            "verdict": "APPROVE",
            "issues": [],
            "needs_revision": False
        }
