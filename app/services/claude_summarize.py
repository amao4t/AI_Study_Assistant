import requests
import logging
from typing import Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

def summarize_document_with_claude(api_key: str, text: str, max_length: int = 1000) -> Tuple[str, Optional[str]]:
    """
    Summarize a document using Claude API
    
    Args:
        api_key: Claude API key
        text: Document text to summarize
        max_length: Maximum length for the summary
        
    Returns:
        Tuple of (summary, error)
    """
    # Limit text length to prevent API issues
    if len(text) > 50000:
        logger.warning(f"Text too long ({len(text)} chars), truncating to 50000")
        text = text[:50000]
    
    try:
        logger.info(f"Summarizing document of length {len(text)}")
        
        # API endpoint and headers
        api_url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Create prompt for document summarization
        prompt = f"""
Please provide a concise but comprehensive summary of the following document. 
The summary should capture the main points, key arguments, and important conclusions.
Keep the summary focused on the factual content without adding any new information.

DOCUMENT TO SUMMARIZE:
{text}

SUMMARY:
"""
        
        # Prepare API request
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": max_length // 4,  # Conservative estimate of token count
            "temperature": 0.3,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Make API call
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Extract summary
        if 'content' in result and len(result['content']) > 0:
            summary = result['content'][0]['text'].strip()
            logger.info("Successfully summarized document")
            return summary, None
        else:
            logger.error("Invalid response from Claude API")
            return "", "Failed to generate summary"
        
    except Exception as e:
        logger.exception(f"Error summarizing document: {str(e)}")
        return "", str(e)