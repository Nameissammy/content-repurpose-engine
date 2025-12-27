from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from app.ai.nodes.context_analyzer import analyze_context
from app.ai.nodes.style_retriever import retrieve_style_guide
from app.ai.nodes.twitter_generator import generate_twitter_thread
from app.ai.nodes.linkedin_generator import generate_linkedin_post
from app.ai.nodes.newsletter_generator import generate_newsletter
from app.ai.nodes.critic import critique_and_refine
import structlog

logger = structlog.get_logger()


class ContentState(TypedDict):
    """State schema for the LangGraph workflow"""
    # Input
    transcript: str
    metadata: Dict[str, Any]
    
    # Analysis
    context_analysis: str
    style_guide: str
    
    # Generated content (one per platform)
    twitter_content: Dict[str, Any]
    linkedin_content: Dict[str, Any]
    newsletter_content: Dict[str, Any]
    
    # Refined content
    twitter_refined: Dict[str, Any]
    linkedin_refined: Dict[str, Any]
    newsletter_refined: Dict[str, Any]


def analyze_node(state: ContentState) -> ContentState:
    """Node 1: Analyze transcript and extract context"""
    logger.info("state_machine_analyze")
    result = analyze_context(state["transcript"], state.get("metadata"))
    state["context_analysis"] = result["analysis"]
    return state


def style_node(state: ContentState) -> ContentState:
    """Node 2: Retrieve style guide"""
    logger.info("state_machine_style_retrieval")
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        result = retrieve_style_guide(db)
        state["style_guide"] = result["style_guide"]
    finally:
        db.close()
    return state


def twitter_node(state: ContentState) -> ContentState:
    """Node 3a: Generate Twitter thread"""
    logger.info("state_machine_twitter_generation")
    result = generate_twitter_thread(
        state["context_analysis"],
        state["style_guide"]
    )
    state["twitter_content"] = result
    return state


def linkedin_node(state: ContentState) -> ContentState:
    """Node 3b: Generate LinkedIn post"""
    logger.info("state_machine_linkedin_generation")
    result = generate_linkedin_post(
        state["context_analysis"],
        state["style_guide"]
    )
    state["linkedin_content"] = result
    return state


def newsletter_node(state: ContentState) -> ContentState:
    """Node 3c: Generate Newsletter"""
    logger.info("state_machine_newsletter_generation")
    result = generate_newsletter(
        state["context_analysis"],
        state["style_guide"]
    )
    state["newsletter_content"] = result
    return state


def critique_twitter_node(state: ContentState) -> ContentState:
    """Node 4a: Critique and refine Twitter content"""
    logger.info("state_machine_critique_twitter")
    result = critique_and_refine(
        state["context_analysis"],
        state["style_guide"],
        state["twitter_content"]["content"],
        "Twitter"
    )
    state["twitter_refined"] = {
        **state["twitter_content"],
        "content": result["refined_content"],
        "critique": result
    }
    return state


def critique_linkedin_node(state: ContentState) -> ContentState:
    """Node 4b: Critique and refine LinkedIn content"""
    logger.info("state_machine_critique_linkedin")
    result = critique_and_refine(
        state["context_analysis"],
        state["style_guide"],
        state["linkedin_content"]["content"],
        "LinkedIn"
    )
    state["linkedin_refined"] = {
        **state["linkedin_content"],
        "content": result["refined_content"],
        "critique": result
    }
    return state


def critique_newsletter_node(state: ContentState) -> ContentState:
    """Node 4c: Critique and refine Newsletter content"""
    logger.info("state_machine_critique_newsletter")
    result = critique_and_refine(
        state["context_analysis"],
        state["style_guide"],
        state["newsletter_content"]["content"],
        "Newsletter"
    )
    state["newsletter_refined"] = {
        **state["newsletter_content"],
        "content": result["refined_content"],
        "critique": result
    }
    return state


def create_workflow() -> StateGraph:
    """
    Create the LangGraph state machine workflow.
    
    Flow:
    1. Analyze transcript -> Extract context
    2. Retrieve style guide
    3. Generate content for all platforms (parallel)
    4. Critique and refine all content (parallel)
    """
    workflow = StateGraph(ContentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("style", style_node)
    workflow.add_node("twitter", twitter_node)
    workflow.add_node("linkedin", linkedin_node)
    workflow.add_node("newsletter", newsletter_node)
    workflow.add_node("critique_twitter", critique_twitter_node)
    workflow.add_node("critique_linkedin", critique_linkedin_node)
    workflow.add_node("critique_newsletter", critique_newsletter_node)
    
    # Define flow
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "style")
    
    # After style retrieval, branch to parallel generation
    workflow.add_edge("style", "twitter")
    workflow.add_edge("style", "linkedin")
    workflow.add_edge("style", "newsletter")
    
    # After generation, move to critique
    workflow.add_edge("twitter", "critique_twitter")
    workflow.add_edge("linkedin", "critique_linkedin")
    workflow.add_edge("newsletter", "critique_newsletter")
    
    # All critiques end the workflow
    workflow.add_edge("critique_twitter", END)
    workflow.add_edge("critique_linkedin", END)
    workflow.add_edge("critique_newsletter", END)
    
    return workflow.compile()


# Create compiled workflow instance
compiled_workflow = create_workflow()


def run_content_generation(transcript: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Run the complete content generation workflow.
    
    Args:
        transcript: Video transcript text
        metadata: Optional video metadata
    
    Returns:
        Dictionary with generated and refined content for all platforms
    """
    logger.info("running_content_generation_workflow")
    
    initial_state: ContentState = {
        "transcript": transcript,
        "metadata": metadata or {},
        "context_analysis": "",
        "style_guide": "",
        "twitter_content": {},
        "linkedin_content": {},
        "newsletter_content": {},
        "twitter_refined": {},
        "linkedin_refined": {},
        "newsletter_refined": {},
    }
    
    # Run the workflow
    final_state = compiled_workflow.invoke(initial_state)
    
    logger.info("content_generation_workflow_complete")
    
    return {
        "twitter": final_state.get("twitter_refined", {}),
        "linkedin": final_state.get("linkedin_refined", {}),
        "newsletter": final_state.get("newsletter_refined", {}),
    }
