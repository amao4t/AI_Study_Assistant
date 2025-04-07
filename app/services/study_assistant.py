import json
import requests
import logging
from typing import Dict, List, Tuple, Optional

from app.utils.api_utils import safe_api_call

# Set up logging
logger = logging.getLogger(__name__)

class StudyAssistant:
    """Service for providing study advice and planning using Claude API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        logger.info("Initialized StudyAssistant with Claude API")
        
        # System prompt for the study assistant
        self.system_prompt = """
You are a helpful study assistant designed to help students with their academic challenges.
Your goal is to provide practical, evidence-based advice on:
- Study techniques and strategies
- Time management and productivity
- Exam preparation and test-taking strategies
- Subject-specific learning methods
- Motivation and overcoming procrastination

Keep your responses concise, practical, and directly applicable. 
When appropriate, suggest specific techniques, tools, or resources.
Base your advice on established learning science and educational research.

Please format your responses for readability:
- Use bullet points or numbered lists for step-by-step instructions or multiple points
- Add line breaks between paragraphs
- Use concise paragraphs (3-5 sentences max)
- Highlight important concepts or terms
"""

    def _call_claude_api(self, prompt, system_prompt=None, chat_history=None, max_tokens=2000, temperature=0.7):
        """Make an API call to Claude API"""
        # Prepare messages based on chat history and prompt
        messages = []
        
        # Add chat history if provided
        if chat_history:
            for message in chat_history:
                role = "user" if message.get("role") == "user" else "assistant"
                messages.append({
                    "role": role,
                    "content": message.get("message", "")
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Prepare payload
        payload = {
            "model": "claude-3-opus-20240229",
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
        
        result = response.json()
        
        # Extract response
        if 'content' in result and len(result['content']) > 0:
            chat_response = result['content'][0]['text'].strip()
            logger.info("Successfully generated chat response")
            return chat_response
        else:
            logger.error("Invalid response from Claude API")
            raise ValueError("Failed to generate response")
    
    def chat(self, user_message: str, chat_history: List[Dict] = None, 
             use_fallback: bool = True) -> Tuple[str, Optional[str], bool]:
        """Generate a response to the user's message
        
        Args:
            user_message: The user's message
            chat_history: List of previous messages
            use_fallback: Whether to use fallback responses if API fails
            
        Returns:
            Tuple of (response, error, is_fallback)
        """
        if not user_message:
            return "", "No message provided", False
        
        if not chat_history:
            chat_history = []
        
        # Use the safe API call utility
        response, is_fallback, error = safe_api_call(
            self._call_claude_api,
            prompt=user_message,
            system_prompt=self.system_prompt,
            chat_history=chat_history,
            temperature=0.7,
            service_name="Study Assistant Chat",
            fallback_func=self._get_chat_fallback
        )
        
        if error and not response:
            return "", error, False
            
        return response, error, is_fallback
    
    def _get_chat_fallback(self, prompt, system_prompt=None, chat_history=None, **kwargs) -> str:
        """Generate a fallback response when the API is unavailable
        
        Args:
            prompt: The user's message
            
        Returns:
            A fallback response
        """
        # Extract key terms from the user's prompt for more relevant fallback
        user_message = prompt.lower()
        
        # Check for common question patterns
        if any(word in user_message for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your study assistant. I'm currently experiencing some technical difficulties connecting to my knowledge base. Please try again in a few minutes."
        
        if any(word in user_message for word in ['thank', 'thanks']):
            return "You're welcome! I'm happy to help, though I'm currently experiencing some technical difficulties. Please try again later if you have more questions."
            
        if 'study' in user_message and any(word in user_message for word in ['how', 'tips', 'advice']):
            return """I'm having trouble connecting to my full knowledge base right now, but here are some general study tips:

1. Use active recall instead of passive review
2. Space out your study sessions over time instead of cramming
3. Teach concepts to others to ensure your understanding
4. Take regular breaks (try the Pomodoro technique)
5. Get enough sleep - it's crucial for memory consolidation

Please try again later for more personalized advice."""
            
        # Default fallback message
        return """I apologize, but I'm currently having trouble connecting to my knowledge base. This might be due to high demand or a temporary service outage.

Here's what you can do:
1. Try again in a few minutes
2. Refresh the page
3. Check your internet connection
4. Try a more specific question when the service is back

In the meantime, remember that effective studying involves active engagement with the material, regular breaks, and testing your knowledge rather than just reviewing it."""

    def generate_study_plan(self, subject: str, goal: str, timeframe: str, hours_per_week: int) -> Tuple[Dict, Optional[str]]:
        """Generate a personalized study plan using safe API call"""
        if not subject or not goal or not timeframe:
            return {}, "Missing required parameters"
        
        try:
            logger.info(f"Generating study plan for {subject}, goal: {goal}, timeframe: {timeframe}")
            
            prompt = f"""
Create a detailed study plan for a student with the following parameters:

Subject: {subject}
Goal: {goal}
Timeframe: {timeframe}
Available study time: {hours_per_week} hours per week

The study plan should include:
1. Weekly breakdown of what to study
2. Recommended resources and materials
3. Study techniques tailored to the subject
4. Milestones and progress checks
5. Review schedule and practice tests (if applicable)

Format your response as a structured JSON object with the following fields:
- overview (string: brief overview of the plan)
- weeks (array of objects, each with 'week_number', 'focus_areas', 'activities', 'resources', and 'hours' fields)
- techniques (array of recommended study techniques)
- milestones (array of progress checkpoints)

Respond ONLY with valid JSON.
"""
            # Use safe API call for better error handling
            plan_json, is_fallback, error = safe_api_call(
                self._get_study_plan_json,
                prompt=prompt,
                service_name="Study Plan Generator",
                fallback_func=self._get_study_plan_fallback
            )
            
            if error and not plan_json:
                return {}, error
                
            return plan_json, None
            
        except Exception as e:
            logger.exception(f"Error generating study plan: {str(e)}")
            return {}, str(e)
            
    def _get_study_plan_json(self, prompt):
        """Get study plan from Claude API and parse as JSON"""
        # Make API call
        response = self._call_claude_api(prompt, max_tokens=2000, temperature=0.7)
        
        # Parse the JSON response
        try:
            # Find JSON in the response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                study_plan = json.loads(json_str)
                logger.info("Successfully generated and parsed study plan")
                return study_plan
            else:
                # If no JSON found, return the raw text as overview
                logger.warning("No JSON found in study plan response")
                return {"overview": response, "weeks": [], "techniques": [], "milestones": []}
                
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw text as overview
            logger.exception(f"Error parsing study plan JSON: {str(e)}")
            return {"overview": response, "weeks": [], "techniques": [], "milestones": []}
    
    def _get_study_plan_fallback(self, prompt):
        """Generate a fallback study plan when the API is unavailable"""
        # Extract subject from the prompt
        import re
        subject_match = re.search(r"Subject: ([^\n]+)", prompt)
        subject = subject_match.group(1) if subject_match else "this subject"
        
        fallback_plan = {
            "overview": f"Here's a general study plan for {subject}. Note that this is a fallback plan as our AI service is currently unavailable. Please try again later for a more personalized plan.",
            "weeks": [
                {
                    "week_number": 1,
                    "focus_areas": "Fundamentals and core concepts",
                    "activities": ["Review basic principles", "Create concept maps", "Set up study schedule"],
                    "resources": "Textbooks, online courses, lecture notes",
                    "hours": 10
                },
                {
                    "week_number": 2,
                    "focus_areas": "In-depth understanding of key topics",
                    "activities": ["Active recall practice", "Problem-solving", "Create flashcards"],
                    "resources": "Practice problems, study guides",
                    "hours": 10
                }
            ],
            "techniques": [
                "Spaced repetition",
                "Active recall",
                "Pomodoro technique (25-minute focused study, 5-minute break)",
                "Feynman technique (teaching concepts to solidify understanding)"
            ],
            "milestones": [
                "Complete understanding of foundational concepts",
                "Ability to solve practice problems without assistance",
                "Successfully complete practice tests with >80% accuracy"
            ]
        }
        
        return fallback_plan
        
    # Similar improvements can be made to other methods
    # Adding only what's necessary for basic functionality

    def recommend_resources(self, subject: str, level: str, resource_type: str = "all") -> Tuple[List[Dict], Optional[str]]:
        """Recommend study resources for a subject with improved error handling"""
        if not subject or not level:
            return [], "Missing required parameters"
        
        try:
            logger.info(f"Recommending resources for {subject}, level: {level}, type: {resource_type}")
            
            prompt = f"""
Recommend 5-7 high-quality educational resources for studying {subject} at the {level} level.

{"Focus on " + resource_type + " resources." if resource_type != "all" else "Include a mix of different resource types (books, online courses, videos, etc.)."}

For each resource, provide:
1. Title or name
2. Type (book, website, course, video series, app, etc.)
3. Brief description of what makes it valuable
4. Appropriate skill level (beginner, intermediate, advanced)

Format your response as a structured JSON array of objects, each with 'title', 'type', 'description', and 'level' fields.

Respond ONLY with valid JSON.
"""
            
            # Use safe_api_call for better error handling
            resources, is_fallback, error = safe_api_call(
                self._get_resources_json,
                prompt=prompt,
                service_name="Resource Recommender",
                fallback_func=self._get_resources_fallback
            )
            
            if error and not resources:
                return [], error
                
            return resources, None
            
        except Exception as e:
            logger.exception(f"Error recommending resources: {str(e)}")
            return [], str(e)
    
    def _get_resources_json(self, prompt):
        """Get resources from Claude API and parse as JSON"""
        # Make API call
        response = self._call_claude_api(prompt, max_tokens=1500, temperature=0.7)
        
        # Parse the JSON response
        try:
            # Find JSON array in the response
            json_start = response.find('[')
            json_end = response.rfind(']')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                resources = json.loads(json_str)
                logger.info("Successfully generated and parsed resources")
                return resources
            else:
                logger.warning("No JSON array found in resources response")
                return []
                
        except json.JSONDecodeError as e:
            logger.exception(f"Error parsing resources JSON: {str(e)}")
            return []
    
    def _get_resources_fallback(self, prompt):
        """Generate fallback resources when the API is unavailable"""
        # Extract subject from the prompt
        import re
        subject_match = re.search(r"studying ([^.]+) at", prompt)
        subject = subject_match.group(1) if subject_match else "this subject"
        
        # Generic fallback resources that could apply to most subjects
        return [
            {
                "title": "Khan Academy",
                "type": "website",
                "description": f"Free comprehensive learning platform with video lessons, interactive exercises, and practice tests for {subject} and many other subjects.",
                "level": "beginner to intermediate"
            },
            {
                "title": "Coursera",
                "type": "online course platform",
                "description": f"Offers courses from top universities and institutions on {subject}, many of which are free to audit.",
                "level": "beginner to advanced"
            },
            {
                "title": "YouTube Educational Channels",
                "type": "video",
                "description": f"Search for '{subject} tutorial' or '{subject} lecture' on YouTube to find free educational content from various creators.",
                "level": "all levels"
            }
        ]