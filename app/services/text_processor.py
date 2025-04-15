import requests
import logging
from typing import Dict, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

class TextProcessor:
    """Service for processing text using Claude API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        logger.info("Initialized TextProcessor with Claude API")
    
    def _call_claude_api(self, prompt, max_tokens=1000, temperature=0.7):
        """Make an API call to Claude"""
        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(self.claude_api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception(f"Error calling Claude API: {str(e)}")
            if hasattr(response, 'text'):
                logger.error(f"API response: {response.text}")
            raise
    
    def summarize(self, text: str, length: str = 'medium', format: str = 'paragraph') -> Tuple[str, Optional[str]]:
        """Summarize text using Claude API
        
        Args:
            text: Text to summarize
            length: Length of summary ('short', 'medium', 'long')
            format: Format of summary ('paragraph', 'bullets')
            
        Returns:
            Tuple of (summary, error)
        """
        if not text or len(text.strip()) < 50:
            return "", "Text is too short to summarize"
        
        try:
            # Limit text length to avoid API issues
            if len(text) > 10000:
                logger.warning(f"Text too long ({len(text)} chars), truncating to 10000")
                text = text[:10000]
                
            logger.info(f"Summarizing text of length {len(text)}, format: {format}, length: {length}")
            
            # Convert length to word count
            length_words = {
                'short': 100,
                'medium': 250,
                'long': 500
            }.get(length, 250)
            
            # Create prompt based on format
            if format == 'bullets':
                prompt = f"""
Summarize the following text in a bulleted list format. Keep it around {length_words} words.

TEXT TO SUMMARIZE:
{text}

SUMMARY (in bullet points):
"""
            else:  # paragraph format
                prompt = f"""
Summarize the following text in paragraph format. Keep it around {length_words} words.

TEXT TO SUMMARIZE:
{text}

SUMMARY:
"""
            
            response = self._call_claude_api(prompt, max_tokens=1000, temperature=0.3)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return "", "Failed to summarize text"
            
            summary = response['content'][0]['text'].strip()
            logger.info("Successfully summarized text")
            return summary, None
        
        except Exception as e:
            logger.exception(f"Error summarizing text: {str(e)}")
            return "", str(e)
    
    def correct_text(self, text: str) -> Tuple[str, Optional[str], Optional[list]]:
        """Correct grammar and improve clarity of text
        
        Args:
            text: Text to correct
            
        Returns:
            Tuple of (corrected_text, error, corrections)
        """
        if not text or len(text.strip()) < 5:
            return "", "Text is too short to correct", None
        
        try:
            # Limit text length to avoid API issues
            if len(text) > 5000:
                logger.warning(f"Text too long ({len(text)} chars), truncating to 5000")
                text = text[:5000]
                
            logger.info(f"Correcting text of length {len(text)}")
            
            prompt = f"""
Correct the grammar, spelling, and improve clarity of the following text while preserving the original meaning.

Your response MUST be formatted in two distinct sections separated by the marker "===CORRECTIONS_JSON===":

SECTION 1: The fully corrected text only, with no explanations or comments. This should be exactly the original text but with corrections applied.

SECTION 2: After the marker, provide a JSON array of corrections with this exact format:
[
  {{
    "original": "the exact original text that was changed",
    "corrected": "the exact correction that replaced it",
    "explanation": "brief explanation of why this correction was made"
  }}
]

Important guidelines:
- Each "original" should be an exact string from the original text
- Each "corrected" should be an exact string from your corrected text
- Make sure the "corrected" strings actually appear in your corrected text
- Don't include overlapping corrections 
- Limit to the most important corrections (maximum 10)
- Don't create large paragraph-sized corrections

ORIGINAL TEXT:
{text}

CORRECTED TEXT:
"""
            
            response = self._call_claude_api(prompt, max_tokens=len(text) * 2, temperature=0.2)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return "", "Failed to correct text", None
            
            response_text = response['content'][0]['text'].strip()
            
            # Extract corrected text and list of corrections using the marker
            parts = response_text.split("===CORRECTIONS_JSON===", 1)
            corrected_text = parts[0].strip()
            
            corrections = []
            if len(parts) > 1:
                # Try to extract JSON list of corrections
                try:
                    import json
                    import re
                    
                    # Find JSON array in the text
                    json_match = re.search(r'\[\s*\{.*\}\s*\]', parts[1], re.DOTALL)
                    if json_match:
                        corrections_text = json_match.group(0)
                        corrections = json.loads(corrections_text)
                        
                        # Additional verification - make sure corrections actually exist in text
                        verified_corrections = []
                        for correction in corrections:
                            if correction['corrected'] in corrected_text:
                                verified_corrections.append(correction)
                            else:
                                logger.warning(f"Correction not found in text: {correction}")
                        
                        corrections = verified_corrections
                except Exception as e:
                    logger.warning(f"Failed to parse corrections list: {e}")
            
            logger.info("Successfully corrected text")
            return corrected_text, None, corrections
        
        except Exception as e:
            logger.exception(f"Error correcting text: {str(e)}")
            return "", str(e), None
    
    def rephrase_text(self, text: str, style: str = 'academic') -> Tuple[str, Optional[str]]:
        """Rephrase text in different style
        
        Args:
            text: Text to rephrase
            style: Style to use ('academic', 'simple', 'creative', 'professional')
            
        Returns:
            Tuple of (rephrased_text, error)
        """
        if not text or len(text.strip()) < 10:
            return "", "Text is too short to rephrase"
        
        style_description = {
            'academic': "formal academic style with sophisticated vocabulary and complex sentence structures",
            'simple': "simple, easy-to-understand language with short sentences",
            'creative': "creative, engaging style with vivid descriptions and metaphors",
            'professional': "professional, business-appropriate style that is clear and concise"
        }
        
        style_prompt = style_description.get(style.lower(), "clear, well-structured")
        
        try:
            # Limit text length to avoid API issues
            if len(text) > 5000:
                logger.warning(f"Text too long ({len(text)} chars), truncating to 5000")
                text = text[:5000]
                
            logger.info(f"Rephrasing text of length {len(text)}, style: {style}")
            
            prompt = f"""
Rephrase the following text in a {style_prompt} style. Preserve the original meaning completely.
Do not add any explanations or comments - only provide the rephrased text.

ORIGINAL TEXT:
{text}

REPHRASED TEXT:
"""
            
            response = self._call_claude_api(prompt, max_tokens=len(text) * 2, temperature=0.7)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return "", "Failed to rephrase text"
            
            rephrased_text = response['content'][0]['text'].strip()
            logger.info("Successfully rephrased text")
            return rephrased_text, None
        
        except Exception as e:
            logger.exception(f"Error rephrasing text: {str(e)}")
            return "", str(e)
    
    def explain_text(self, text: str, level: str = 'high_school') -> Tuple[str, Optional[str]]:
        """Explain complex text in simpler terms
        
        Args:
            text: Text to explain
            level: Target audience level ('elementary', 'middle_school', 'high_school', 'college')
            
        Returns:
            Tuple of (explanation, error)
        """
        if not text or len(text.strip()) < 10:
            return "", "Text is too short to explain"
        
        level_description = {
            'elementary': "an elementary school student (8-10 years old)",
            'middle_school': "a middle school student (11-13 years old)",
            'high_school': "a high school student (14-18 years old)",
            'college': "a college student"
        }
        
        level_prompt = level_description.get(level.lower(), "a general audience")
        
        try:
            # Limit text length to avoid API issues
            if len(text) > 5000:
                logger.warning(f"Text too long ({len(text)} chars), truncating to 5000")
                text = text[:5000]
                
            logger.info(f"Explaining text of length {len(text)}, level: {level}")
            
            prompt = f"""
Explain the following text to {level_prompt}. Break down complex concepts, use appropriate language, and make the content accessible.

TEXT TO EXPLAIN:
{text}

EXPLANATION:
"""
            
            response = self._call_claude_api(prompt, max_tokens=len(text) * 2, temperature=0.5)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return "", "Failed to explain text"
            
            explanation = response['content'][0]['text'].strip()
            logger.info("Successfully explained text")
            return explanation, None
        
        except Exception as e:
            logger.exception(f"Error explaining text: {str(e)}")
            return "", str(e)