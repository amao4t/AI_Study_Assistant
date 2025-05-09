import base64
import requests
import logging
import json
from typing import Dict, List, Tuple, Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

class ClaudeService:
    """Service for interacting with Claude API, including vision capabilities"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        logger.info("Initialized ClaudeService with Claude API")
    
    def _call_claude_api(self, messages, system_prompt=None, max_tokens=2000, temperature=0.7, model="claude-3-opus-20240229"):
        """Make an API call to Claude API"""
        # Prepare payload
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        # Add system prompt as a top-level parameter if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Log API request (without sensitive data)
        logger.debug(f"Making Claude API request with {len(messages)} messages, system prompt: {bool(system_prompt)}")
        
        # Make API call
        response = requests.post(self.claude_api_url, json=payload, headers=self.headers, timeout=30)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        
        # Log successful response
        logger.debug(f"Successful API response, status: {response.status_code}")
        
        return response.json()
    
    def process_image_ocr(self, image_data):
        """Process an image with OCR using Claude Vision capabilities
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Extracted text from the image
        """
        try:
            # Log the image size for debugging
            image_size = len(image_data)
            logger.debug(f"Processing image with OCR, size: {image_size} bytes")
            
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare messages with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",  # Assuming JPEG, but Claude handles various formats
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": "Please extract all the text from this image. Return only the extracted text without any additional commentary. Maintain the original formatting as much as possible including paragraphs, bullet points, and table structures."
                        }
                    ]
                }
            ]
            
            # Set appropriate system prompt for OCR
            system_prompt = "You are an OCR assistant. Your task is to accurately extract text from images. Return only the extracted text without any commentary, explanations, or additional formatting. Preserve the original text layout including paragraphs, bullet points, and table structures as much as possible."
            
            # Make API call
            try:
                result = self._call_claude_api(
                    messages=messages,
                    system_prompt=system_prompt,
                    max_tokens=4000,  # Higher token limit for potentially long documents
                    temperature=0.2,  # Lower temperature for more accurate text extraction
                    model="claude-3-opus-20240229"  # Using opus for best quality
                )
                
                # Extract text from response
                if 'content' in result and len(result['content']) > 0:
                    extracted_text = result['content'][0]['text'].strip()
                    text_length = len(extracted_text)
                    logger.info(f"Successfully extracted text from image ({text_length} chars)")
                    
                    # Log a snippet of the extracted text for debugging
                    if text_length > 0:
                        snippet = extracted_text[:100] + ('...' if text_length > 100 else '')
                        logger.debug(f"Extracted text preview: {snippet}")
                    
                    return extracted_text
                else:
                    logger.error("Invalid response from Claude API for OCR")
                    logger.info("Attempting local OCR fallback")
                    return self._fallback_local_ocr(image_data)
            except Exception as api_error:
                logger.error(f"Error processing image with Claude OCR: {str(api_error)}")
                logger.info("Attempting local OCR fallback")
                return self._fallback_local_ocr(image_data)
                
        except Exception as e:
            logger.exception(f"Error processing image with OCR: {str(e)}")
            return self._fallback_local_ocr(image_data)
            
    def chat_with_text(self, text, user_question, chat_history=None):
        """Chat with text content using Claude
        
        Args:
            text: The text to chat about
            user_question: The user's question
            chat_history: Previous chat messages
            
        Returns:
            Claude's response
        """
        try:
            # Prepare system prompt
            system_prompt = f"""You are a helpful AI assistant that answers questions about documents.
Your answers should be based solely on the document content provided.
If you don't know the answer or if the question is not related to the document content, say so politely.
Keep your responses concise and directly answer the user's question."""
            
            # Prepare messages
            messages = []
            
            # Initial context message with the document text
            messages.append({
                "role": "user",
                "content": f"Here is the document content to reference when answering questions:\n\n{text[:100000]}"
            })
            
            # Add AI acknowledgment
            messages.append({
                "role": "assistant",
                "content": "I'll answer questions about this document."
            })
            
            # Add chat history if provided
            if chat_history:
                for message in chat_history:
                    role = "user" if message.get("role") == "user" else "assistant"
                    messages.append({
                        "role": role,
                        "content": message.get("message", "")
                    })
            
            # Add current user question
            messages.append({
                "role": "user",
                "content": user_question
            })
            
            # Make API call
            result = self._call_claude_api(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.7
            )
            
            # Extract response
            if 'content' in result and len(result['content']) > 0:
                response = result['content'][0]['text'].strip()
                return response
            else:
                logger.error("Invalid response from Claude API for chat")
                return "I'm sorry, I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.exception(f"Error in chat_with_text: {str(e)}")
            return f"I'm sorry, an error occurred: {str(e)}"
            
    def summarize_text(self, text):
        """Summarize text content using Claude
        
        Args:
            text: The text to summarize
            
        Returns:
            Summary of the text
        """
        try:
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": f"""Please provide a comprehensive summary of the following text. 
Capture the main points, key arguments, and important conclusions.
Focus on the factual content without adding any new information.

TEXT TO SUMMARIZE:
{text[:100000]}"""
                }
            ]
            
            # Make API call
            result = self._call_claude_api(
                messages=messages,
                max_tokens=2000,
                temperature=0.3
            )
            
            # Extract summary
            if 'content' in result and len(result['content']) > 0:
                summary = result['content'][0]['text'].strip()
                return summary
            else:
                logger.error("Invalid response from Claude API for summary")
                return "Unable to generate summary."
                
        except Exception as e:
            logger.exception(f"Error in summarize_text: {str(e)}")
            return f"Error generating summary: {str(e)}"

    def _fallback_local_ocr(self, image_data):
        """Fallback to local OCR processing if Claude Vision fails
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Extracted text from the image or empty string if failed
        """
        try:
            # Import optional dependencies
            import pytesseract
            from PIL import Image
            import io
            
            logger.info("Attempting local OCR fallback")
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Process with Tesseract OCR
            extracted_text = pytesseract.image_to_string(image)
            
            if extracted_text:
                logger.info(f"Local OCR extracted {len(extracted_text)} characters")
                return extracted_text
            else:
                logger.warning("Local OCR extraction returned empty result")
                return ""
        except ImportError:
            logger.warning("Pytesseract not installed, cannot perform local OCR")
            return ""
        except Exception as e:
            logger.exception(f"Error in local OCR fallback: {str(e)}")
            return "" 