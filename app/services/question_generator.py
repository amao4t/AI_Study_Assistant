import json
import re
import requests
import logging
from typing import Dict, List, Tuple, Optional

from app import db
from app.models.document import Document, Question, DocumentChunk

# Set up logging
logger = logging.getLogger(__name__)

class QuestionGenerator:
    """Service for generating questions using Claude API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        logger.info("Initialized QuestionGenerator with Claude API")
    
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
    
    def generate_mcq(self, context: str) -> Dict:
        """Generate a multiple-choice question from context text"""
        try:
            logger.info(f"Generating MCQ from context of length: {len(context)}")
            
            # Limit context length to prevent API issues
            if len(context) > 2000:
                logger.info(f"Context too long ({len(context)} chars), truncating to 2000")
                context = context[:2000]
            
            prompt = """
Based on the context below, create one high-quality multiple-choice question.
Follow this exact format in your response:

Question: [The question text here]
Options:
(A) [Option A text]
(B) [Option B text]
(C) [Option C text]
(D) [Option D text]
Answer: [Correct letter (A, B, C, or D)]

Make sure the question tests understanding of the context, options are plausible, and exactly one answer is correct.

Context:
"""
            prompt += context
            
            response = self._call_claude_api(prompt, max_tokens=500, temperature=0.7)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return {}
                
            result = response['content'][0]['text']
            logger.info("Successfully generated MCQ")
            
            parsed = self._parse_mcq_response(result)
            return parsed
        
        except Exception as e:
            logger.exception(f"Error generating MCQ: {str(e)}")
            return {}
    
    def generate_qa(self, context: str) -> Dict:
        """Generate a question and answer pair from context text"""
        try:
            logger.info(f"Generating QA from context of length: {len(context)}")
            
            # Limit context length to prevent API issues
            if len(context) > 2000:
                logger.info(f"Context too long ({len(context)} chars), truncating to 2000")
                context = context[:2000]
            
            prompt = """
Based on the context below, create one high-quality question and its answer.
Follow this exact format in your response:

QUESTION: [The question text here]
ANSWER: [The answer text here]

Make sure the question requires understanding of the context and the answer is accurate and complete.

Context:
"""
            prompt += context
            
            response = self._call_claude_api(prompt, max_tokens=300, temperature=0.7)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return {}
                
            result = response['content'][0]['text']
            logger.info("Successfully generated QA")
            
            parsed = self._parse_qa_response(result)
            return parsed
        
        except Exception as e:
            logger.exception(f"Error generating QA: {str(e)}")
            return {}
    
    def _parse_mcq_response(self, response: str) -> Dict:
        """Parse MCQ response from Claude API"""
        logger.debug(f"Parsing MCQ response: {response[:100]}...")
        
        pattern = re.compile(r'Question:\s*(.*?)\s*Options:\s*(.*?)\s*Answer:\s*([A-D])', re.DOTALL | re.IGNORECASE)
        match = pattern.search(response)
        
        if not match:
            logger.warning("Failed to parse MCQ response with regex")
            return {}
        
        try:
            question = match.group(1).strip()
            options_text = match.group(2).strip()
            answer = match.group(3).strip().upper()
            
            # Parse options
            options = {}
            option_pattern = re.compile(r'\(([A-D])\)\s*(.*?)(?=\([A-D]\)|$)', re.DOTALL | re.IGNORECASE)
            option_matches = option_pattern.findall(options_text)
            
            for key, value in option_matches:
                options[key.upper()] = value.strip()
            
            # Verify all required data is present
            if question and options and len(options) == 4 and answer in options:
                result = {
                    'question': question,
                    'options': options,
                    'answer': answer
                }
                logger.info("Successfully parsed MCQ")
                return result
            
            logger.warning("Missing required data in parsed MCQ")
            return {}
        except Exception as e:
            logger.exception(f"Error parsing MCQ response: {str(e)}")
            return {}
            
    def _parse_qa_response(self, response: str) -> Dict:
        """Parse Q&A response from Claude API"""
        logger.debug(f"Parsing QA response: {response[:100]}...")
        
        pattern = re.compile(r"QUESTION:\s*(.*?)\s*ANSWER:\s*(.*)", re.DOTALL | re.IGNORECASE)
        match = pattern.search(response)
        
        if not match:
            logger.warning("Failed to parse QA response with regex")
            return {}
        
        try:
            question = match.group(1).strip()
            answer = match.group(2).strip()
            
            if question and answer:
                result = {
                    'question': question,
                    'answer': answer
                }
                logger.info("Successfully parsed QA")
                return result
            
            logger.warning("Missing question or answer in parsed QA")
            return {}
        except Exception as e:
            logger.exception(f"Error parsing QA response: {str(e)}")
            return {}
            
    def generate_questions_for_document(self, document_id: int, user_id: int, 
                                      question_type: str = 'mcq', 
                                      count: int = 5) -> Tuple[List[Dict], Optional[str]]:
        """Generate questions from a document"""
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return [], "Document not found or you don't have permission"
        
        # Get document chunks
        chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
        if not chunks:
            return [], "No text chunks available for this document"
        
        # Limit number of chunks to process
        max_chunks = min(20, len(chunks))  # Process max 20 chunks
        logger.info(f"Using {max_chunks} chunks out of {len(chunks)} for question generation")
        
        # Shuffle chunks to get diverse questions
        import random
        random.shuffle(chunks)
        
        # Limit chunks to generate 'count' questions
        chunks = chunks[:min(count*2, max_chunks)]
        
        questions = []
        stored_questions = []
        max_attempts = min(count * 3, 10)  # Limit attempts to prevent excessive API calls
        attempts = 0
        
        for chunk in chunks:
            if len(questions) >= count or attempts >= max_attempts:
                break
                
            attempts += 1
            context = chunk.chunk_text
            if not context or len(context.strip()) < 50:  # Skip very short chunks
                continue
            
            try:
                if question_type.lower() == 'mcq':
                    question_data = self.generate_mcq(context)
                    if 'question' in question_data and 'options' in question_data and 'answer' in question_data:
                        # Store options as JSON string
                        options_json = json.dumps(question_data['options'])
                        answer = question_data['answer']
                        answer_text = question_data['options'][answer]
                        
                        # Create question record
                        question = Question(
                            question_text=question_data['question'],
                            question_type='mcq',
                            options=options_json,
                            answer=answer,
                            document_id=document_id,
                            user_id=user_id
                        )
                        
                        db.session.add(question)
                        stored_questions.append(question)
                        
                        # Format for returning to client
                        questions.append({
                            'question': question_data['question'],
                            'options': question_data['options'],
                            'answer': answer,
                            'answer_text': answer_text,
                            'question_type': 'mcq'
                        })
                
                elif question_type.lower() == 'qa':
                    question_data = self.generate_qa(context)
                    if 'question' in question_data and 'answer' in question_data:
                        # Create question record
                        question = Question(
                            question_text=question_data['question'],
                            question_type='qa',
                            options=None,
                            answer=question_data['answer'],
                            document_id=document_id,
                            user_id=user_id
                        )
                        
                        db.session.add(question)
                        stored_questions.append(question)
                        
                        # Format for returning to client
                        questions.append({
                            'question': question_data['question'],
                            'answer': question_data['answer'],
                            'question_type': 'qa'
                        })
            
            except Exception as e:
                logger.exception(f"Error generating question from chunk: {str(e)}")
                continue
        
        # Commit all questions to database
        if stored_questions:
            try:
                db.session.commit()
                logger.info(f"Saved {len(stored_questions)} questions to database")
            except Exception as e:
                logger.exception(f"Error saving questions: {str(e)}")
                db.session.rollback()
                return [], f"Error saving questions: {str(e)}"
        
        if not questions:
            return [], "Could not generate any valid questions from the document"
        
        return questions[:count], None
        
    def evaluate_answer(self, question_id: int, user_answer: str) -> Dict:
        """Evaluate a user's answer to a question"""
        question = Question.query.get(question_id)
        if not question:
            return {'error': 'Question not found'}
        
        # Get correct answer
        correct_answer = question.answer
        
        if question.question_type == 'mcq':
            # For MCQ, check if the answer key matches
            try:
                options = json.loads(question.options)
                is_correct = user_answer.upper() == correct_answer.upper()
                correct_text = options.get(correct_answer, '')
                
                return {
                    'is_correct': is_correct,
                    'correct_answer': correct_answer,
                    'correct_text': correct_text,
                    'score': 1 if is_correct else 0
                }
            except:
                return {'error': 'Error parsing question options'}
        
        elif question.question_type == 'qa':
            # For QA, use Claude to evaluate answer
            try:
                prompt = f"""
Evaluate how well the user's answer matches the correct answer on a scale of 0-3:
0: Completely incorrect or unrelated
1: Partially correct but missing key points
2: Mostly correct with minor omissions
3: Completely correct

Correct answer: {correct_answer}
User answer: {user_answer}

Score (respond with ONLY a single digit 0, 1, 2, or 3):
"""
                
                response = self._call_claude_api(prompt, max_tokens=10, temperature=0.1)
                
                if 'content' not in response or len(response['content']) == 0:
                    logger.error("Invalid response from Claude API during answer evaluation")
                    # Fall back to simple similarity
                    similarity = self._simple_similarity(user_answer.lower(), correct_answer.lower())
                    score = round(similarity * 3)  # Convert to 0-3 scale
                else:
                    result = response['content'][0]['text'].strip()
                    # Extract just the score number
                    score_match = re.search(r'[0-3]', result)
                    if score_match:
                        score = int(score_match.group(0))
                    else:
                        # Fall back to simple similarity if no match
                        similarity = self._simple_similarity(user_answer.lower(), correct_answer.lower())
                        score = round(similarity * 3)  # Convert to 0-3 scale
                
                return {
                    'is_correct': score >= 2,  # Consider 2-3 as correct
                    'correct_answer': correct_answer,
                    'score': score,
                    'max_score': 3
                }
            
            except Exception as e:
                logger.exception(f"Error evaluating QA answer: {str(e)}")
                # Fallback to simple string matching
                similarity = self._simple_similarity(user_answer.lower(), correct_answer.lower())
                score = round(similarity * 3)  # Convert to 0-3 scale
                
                return {
                    'is_correct': score >= 2,
                    'correct_answer': correct_answer,
                    'score': score,
                    'max_score': 3
                }
        
        return {'error': 'Unknown question type'}
    
    def _simple_similarity(self, str1: str, str2: str) -> float:
        """Calculate a simple similarity score between two strings"""
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)