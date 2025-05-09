import os
import logging
import anthropic
from flask import current_app

logger = logging.getLogger(__name__)

def get_anthropic_client():
    """
    Returns an initialized Anthropic client using the API key from config
    """
    api_key = current_app.config.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        logger.error("Missing Anthropic API key")
        return None
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        return client
    except Exception as e:
        logger.exception(f"Error initializing Anthropic client: {str(e)}")
        return None

def chat_with_claude(client, prompt, system_prompt=None, max_tokens=1000, model="claude-3-opus-20240229"):
    """
    Send a chat request to Claude
    
    Args:
        client: Anthropic client object
        prompt: User message/prompt
        system_prompt: Optional system prompt to set context
        max_tokens: Maximum tokens in response
        model: Model to use, default is Claude 3 Opus
        
    Returns:
        Response text or None if error
    """
    if not client:
        logger.error("No Anthropic client provided")
        return None
    
    try:
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
            
        response = client.messages.create(**kwargs)
        
        if response and response.content:
            # Extract the text from the first content block
            for content in response.content:
                if content.type == "text":
                    return content.text
                    
        return None
    except Exception as e:
        logger.exception(f"Error calling Claude API: {str(e)}")
        return None 