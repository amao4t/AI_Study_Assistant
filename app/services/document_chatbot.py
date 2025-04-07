import requests
import logging
from flask import current_app
from typing import Dict, List, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

class DocumentChatbot:
    """ChatBot for interacting with document content using Claude API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        logger.info("Initialized DocumentChatbot with Claude API")
    
    def chat_with_document(self, document_text: str, user_question: str, 
                           chat_history: List[Dict] = None) -> Tuple[str, Optional[str]]:
        """Generate a response to the user's question based on document content
        
        Args:
            document_text: The text of the document
            user_question: The user's question
            chat_history: List of previous messages
            
        Returns:
            Tuple of (response, error)
        """
        if not document_text or not user_question:
            return "", "Missing document text or question"
        
        try:
            logger.info(f"Processing chat: document length {len(document_text)}, question length {len(user_question)}")
            
            # Truncate document if too long - reduce size further to avoid token limits
            max_length = 6000  # Reduced from 8000
            if len(document_text) > max_length:
                logger.warning(f"Document too long ({len(document_text)} chars), truncating to {max_length}")
                document_text = document_text[:max_length]
            
            # Prepare the user message with context
            context_message = f"""Here is the document content:

{document_text}

Based only on the document above, please answer this question: {user_question}"""
            
            # Prepare messages array - starting with just a user message (no system message)
            messages = [
                {"role": "user", "content": context_message}
            ]
            
            # Add minimal chat history if provided (only the most recent exchanges)
            if chat_history and len(chat_history) > 0:
                # Only use the last 2 exchanges to keep token count low
                recent_history = chat_history[-4:] if len(chat_history) > 4 else chat_history
                
                # Clear messages and start with just context for the first message
                if len(recent_history) > 0:
                    messages = []
                    
                    # First add the document context
                    first_user_msg = f"""Here is the document content:

{document_text}

Please refer to this document to answer my questions."""
                    messages.append({"role": "user", "content": first_user_msg})
                    messages.append({"role": "assistant", "content": "I've reviewed the document and I'm ready to answer your questions based solely on its content."})
                    
                    # Then add recent history
                    for message in recent_history:
                        role = "user" if message.get("role") == "user" else "assistant"
                        content = message.get("message", "")
                        # Skip empty messages
                        if not content.strip():
                            continue
                        # Truncate long messages
                        if len(content) > 500:
                            content = content[:500] + "... [truncated]"
                        messages.append({
                            "role": role,
                            "content": content
                        })
                    
                    # Add current question as a separate message
                    messages.append({
                        "role": "user",
                        "content": user_question
                    })
            
            # Prepare payload with a simpler, reliable model
            payload = {
                "model": "claude-3-haiku-20240307",  # Using haiku instead of opus
                "max_tokens": 1000,
                "temperature": 0.3,
                "messages": messages
            }
            
            # Debug log the message structure but not the full content
            logger.debug(f"Sending request to Claude API with {len(messages)} messages")
            
            # Make API call
            response = requests.post(self.claude_api_url, json=payload, headers=self.headers)
            
            # Log the response status and some details without exposing sensitive data
            logger.debug(f"Claude API response status: {response.status_code}")
            
            # Check if there's an error and log more details
            if not response.ok:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return "", f"API Error: {response.status_code}"
                
            # Continue if successful
            result = response.json()
            
            # Extract response
            if 'content' in result and len(result['content']) > 0:
                chat_response = result['content'][0]['text'].strip()
                logger.info("Successfully generated chat response")
                return chat_response, None
            else:
                logger.error("Invalid response from Claude API")
                return "", "Failed to generate response"
            
        except Exception as e:
            logger.exception(f"Error in chat_with_document: {str(e)}")
            return "", str(e)
    
    @classmethod
    def get_instance(cls):
        """Get a singleton instance of DocumentChatbot"""
        if not hasattr(cls, '_instance'):
            api_key = current_app.config.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in app config")
            cls._instance = cls(api_key)
        return cls._instance