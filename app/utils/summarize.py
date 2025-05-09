import logging
from flask import current_app
from .claude import get_anthropic_client, chat_with_claude

logger = logging.getLogger(__name__)

def generate_summary(text, max_length=500):
    """
    Generate a summary of the provided text using Claude API
    
    Args:
        text: Text to summarize
        max_length: Maximum length of summary in tokens
        
    Returns:
        Summary text or None if error
    """
    if not text or len(text.strip()) < 100:
        logger.warning("Text too short to summarize")
        return text
    
    # Get Claude client
    client = get_anthropic_client()
    if not client:
        logger.error("Failed to get Anthropic client")
        return None
    
    # Create prompt for summarization
    prompt = f"""Please provide a concise summary of the following text. 
Focus on the key points and main ideas.

TEXT TO SUMMARIZE:
{text}

SUMMARY:"""
    
    # System prompt to guide the summarization
    system_prompt = """You are an expert summarizer. Your task is to create concise, 
accurate summaries that capture the essential information and main points of the text.
Keep the summary clear, factual, and well-organized."""
    
    # Call Claude API
    try:
        summary = chat_with_claude(
            client=client,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_length,
            model=current_app.config.get('CLAUDE_MODEL', 'claude-3-opus-20240229')
        )
        
        return summary
    except Exception as e:
        logger.exception(f"Error generating summary: {str(e)}")
        return None 