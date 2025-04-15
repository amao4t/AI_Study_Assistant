import json
import re
import requests
import logging
import random
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter
import time

from app import db
from app.models.document import Document, Question, DocumentChunk
from app.utils.api_utils import log_api_access

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
        # Cache for previously generated questions to avoid duplicates
        self.question_cache = {}
        logger.info("Initialized QuestionGenerator with Claude API and caching")
    
    def _call_claude_api(self, prompt, max_tokens=1000, temperature=0.7, model="claude-3-opus-20240229"):
        """Make an API call to Claude"""
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(self.claude_api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            log_api_access("claude_question_api", True)
            return response.json()
        except Exception as e:
            logger.exception(f"Error calling Claude API: {str(e)}")
            log_api_access("claude_question_api", False, {"error": str(e)})
            if hasattr(response, 'text'):
                logger.error(f"API response: {response.text}")
            raise
    
    def _get_content_hash(self, text):
        """Generate a hash for text content to use for caching"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _determine_difficulty(self, question_text, answer):
        """Determine the difficulty level of a question based on its content"""
        # Simple heuristics for difficulty estimation
        question_length = len(question_text)
        answer_length = len(answer)
        
        # Check for complex terms or concepts
        complex_terms = [
            'analyze', 'evaluate', 'explain', 'compare', 'contrast', 'critique',
            'synthesize', 'theorize', 'hypothesize', 'investigate', 'differentiate'
        ]
        
        # Count complexity indicators
        complexity_score = 0
        for term in complex_terms:
            if term in question_text.lower():
                complexity_score += 1
        
        # Determine difficulty based on multiple factors
        if complexity_score >= 2 or (question_length > 100 and answer_length > 150):
            return 'hard'
        elif complexity_score >= 1 or (question_length > 70 and answer_length > 100):
            return 'medium'
        else:
            return 'easy'
    
    def generate_mcq(self, context: str) -> Dict:
        """Generate a multiple-choice question from context text with improved prompt"""
        try:
            logger.info(f"Generating MCQ from context of length: {len(context)}")
            
            # Generate a hash for the context
            context_hash = self._get_content_hash(context)
            
            # Check cache first
            if context_hash in self.question_cache and 'mcq' in self.question_cache[context_hash]:
                logger.info("Using cached MCQ")
                return self.question_cache[context_hash]['mcq']
            
            # Limit context length to prevent API issues
            if len(context) > 2000:
                logger.info(f"Context too long ({len(context)} chars), truncating to 2000")
                context = context[:2000]
            
            prompt = """
Based on the context below, create one high-quality multiple-choice question.

IMPORTANT GUIDELINES:
1. Make sure the question is clear, concise, and tests significant information
2. Create 4 distinct options that are plausible but with exactly one correct answer
3. Avoid obvious incorrect options
4. Ensure options are mutually exclusive and don't overlap
5. Use different wording than the original text where possible
6. Focus on testing understanding rather than mere recall
7. Ensure the question tests important concepts, not trivial details
8. The question should be challenging but fair
9. Avoid questions that can be answered without understanding the context
10. Make sure the question requires critical thinking

Follow this exact format in your response:

Question: [The question text here]
Options:
(A) [Option A text]
(B) [Option B text]
(C) [Option C text]
(D) [Option D text]
Answer: [Correct letter (A, B, C, or D)]

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
            
            # Determine difficulty and add to the parsed result
            if parsed and 'question' in parsed and 'answer' in parsed:
                difficulty = self._determine_difficulty(parsed['question'], parsed['answer'])
                parsed['difficulty'] = difficulty
            
            # Cache the result
            if context_hash not in self.question_cache:
                self.question_cache[context_hash] = {}
            self.question_cache[context_hash]['mcq'] = parsed
            
            return parsed
        
        except Exception as e:
            logger.exception(f"Error generating MCQ: {str(e)}")
            return {}
    
    def generate_qa(self, context: str) -> Dict:
        """Generate a question and answer pair with improved prompt"""
        try:
            logger.info(f"Generating QA from context of length: {len(context)}")
            
            # Limit context length to prevent API issues
            if len(context) > 2000:
                logger.info(f"Context too long ({len(context)} chars), truncating to 2000")
                context = context[:2000]
            
            prompt = """
Based on the context below, create one high-quality question and its detailed answer.

IMPORTANT GUIDELINES:
1. Create a question that tests understanding of important concepts
2. The question should require analysis, not just fact recall
3. Focus on significant information, not trivial details
4. Create a question that cannot be answered with just a single word or phrase
5. The answer should be comprehensive, accurate and directly based on the context
6. Provide enough detail in the answer to fully explain the concept

Follow this exact format in your response:

QUESTION: [The question text here]
ANSWER: [The detailed answer here]

Context:
"""
            prompt += context
            
            response = self._call_claude_api(prompt, max_tokens=400, temperature=0.7)
            
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
    
    def generate_true_false(self, context: str) -> Dict:
        """Generate a true/false question based on context"""
        try:
            logger.info(f"Generating True/False question from context of length: {len(context)}")
            
            # Limit context length to prevent API issues
            if len(context) > 2000:
                logger.info(f"Context too long ({len(context)} chars), truncating to 2000")
                context = context[:2000]
            
            prompt = """
Based on the context below, create one high-quality True/False question.

IMPORTANT GUIDELINES:
1. Create a statement that is clearly either true or false based on the context
2. Avoid ambiguous statements that could be interpreted in multiple ways
3. Focus on important concepts from the context, not trivial details
4. For false statements, make sure they are plausibly false (not obviously wrong)
5. Ensure the statement tests understanding rather than mere recall
6. Include a brief explanation of why the statement is true or false

Follow this exact format in your response:

STATEMENT: [The statement to evaluate as true or false]
ANSWER: [True or False]
EXPLANATION: [Brief explanation of why the statement is true or false]

Context:
"""
            prompt += context
            
            response = self._call_claude_api(prompt, max_tokens=300, temperature=0.7)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return {}
                
            result = response['content'][0]['text']
            logger.info("Successfully generated True/False question")
            
            parsed = self._parse_true_false_response(result)
            return parsed
        
        except Exception as e:
            logger.exception(f"Error generating True/False question: {str(e)}")
            return {}
    
    def generate_fill_in_blank(self, context: str) -> Dict:
        """Generate a fill-in-the-blank question based on context"""
        try:
            logger.info(f"Generating Fill-in-the-blank question from context of length: {len(context)}")
            
            # Limit context length to prevent API issues
            if len(context) > 2000:
                logger.info(f"Context too long ({len(context)} chars), truncating to 2000")
                context = context[:2000]
            
            prompt = """
Based on the context below, create one high-quality fill-in-the-blank question.

IMPORTANT GUIDELINES:
1. Create a sentence with one important term or concept replaced with a blank
2. The missing term should be significant, not a trivial word
3. The blank should test understanding of an important concept
4. The answer should be clear and specific (not multiple possible answers)
5. Provide the complete sentence and then the answer separately
6. Include a brief explanation of why this answer is correct

Follow this exact format in your response:

QUESTION: [Sentence with _____ for the blank]
ANSWER: [The correct word or phrase that goes in the blank]
EXPLANATION: [Brief explanation of the answer]

Context:
"""
            prompt += context
            
            response = self._call_claude_api(prompt, max_tokens=300, temperature=0.7)
            
            if 'content' not in response or len(response['content']) == 0:
                logger.error("Invalid response from Claude API")
                return {}
                
            result = response['content'][0]['text']
            logger.info("Successfully generated fill-in-the-blank question")
            
            parsed = self._parse_fill_in_blank_response(result)
            return parsed
        
        except Exception as e:
            logger.exception(f"Error generating fill-in-the-blank question: {str(e)}")
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
                    'answer': answer,
                    'question_type': 'mcq'
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
                    'answer': answer,
                    'question_type': 'qa'
                }
                logger.info("Successfully parsed QA")
                return result
            
            logger.warning("Missing question or answer in parsed QA")
            return {}
        except Exception as e:
            logger.exception(f"Error parsing QA response: {str(e)}")
            return {}
            
    def _parse_true_false_response(self, response: str) -> Dict:
        """Parse True/False response from Claude API"""
        logger.debug(f"Parsing True/False response: {response[:100]}...")
        
        pattern = re.compile(r"STATEMENT:\s*(.*?)\s*ANSWER:\s*(True|False)\s*EXPLANATION:\s*(.*)", re.DOTALL | re.IGNORECASE)
        match = pattern.search(response)
        
        if not match:
            logger.warning("Failed to parse True/False response with regex")
            return {}
        
        try:
            statement = match.group(1).strip()
            answer = match.group(2).strip()
            explanation = match.group(3).strip()
            
            if statement and answer and explanation:
                result = {
                    'question': statement,
                    'answer': answer,
                    'explanation': explanation,
                    'question_type': 'true_false',
                    'options': {'True': 'True', 'False': 'False'}
                }
                logger.info("Successfully parsed True/False question")
                return result
            
            logger.warning("Missing data in parsed True/False question")
            return {}
        except Exception as e:
            logger.exception(f"Error parsing True/False response: {str(e)}")
            return {}
            
    def _parse_fill_in_blank_response(self, response: str) -> Dict:
        """Parse fill-in-the-blank response from Claude API"""
        logger.debug(f"Parsing fill-in-the-blank response: {response[:100]}...")
        
        pattern = re.compile(r"QUESTION:\s*(.*?)\s*ANSWER:\s*(.*?)\s*EXPLANATION:\s*(.*)", re.DOTALL | re.IGNORECASE)
        match = pattern.search(response)
        
        if not match:
            logger.warning("Failed to parse fill-in-the-blank response with regex")
            return {}
        
        try:
            question = match.group(1).strip()
            answer = match.group(2).strip()
            explanation = match.group(3).strip()
            
            if question and answer:
                result = {
                    'question': question,
                    'answer': answer,
                    'explanation': explanation,
                    'question_type': 'fill_in_blank'
                }
                logger.info("Successfully parsed fill-in-the-blank question")
                return result
            
            logger.warning("Missing question or answer in parsed fill-in-the-blank")
            return {}
        except Exception as e:
            logger.exception(f"Error parsing fill-in-the-blank response: {str(e)}")
            return {}
    
    def generate_questions_for_document(self, document_id: int, user_id: int, 
                                      question_type: str = 'mcq', 
                                      count: int = None,
                                      difficulty_levels: List[str] = None) -> Tuple[List[Dict], Optional[str]]:
        """Generate questions for a document with improved caching and variety"""
        document = Document.query.filter_by(id=document_id).first()
        if not document:
            return [], "Document not found"
        
        # Check if user is authorized to access this document
        if document.user_id != user_id:
            return [], "Unauthorized access to document"
        
        try:
            # Set default difficulty levels if not provided
            if difficulty_levels is None:
                difficulty_levels = ['easy', 'medium', 'hard']
            
            # Determine number of questions based on document size if count not specified
            if count is None:
                # Get document chunks to determine length
                chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
                total_text_length = sum(len(chunk.chunk_text) for chunk in chunks) if chunks else 0
                
                # Scale count based on document length (between 10-30 questions)
                if total_text_length > 10000:  # Large document
                    count = 30
                elif total_text_length > 5000:  # Medium document
                    count = 20
                else:  # Small document
                    count = 10
            
            logger.info(f"Generating {count} questions of type {question_type} with difficulties {difficulty_levels} for document {document_id}")
            
            # Get document chunks
            chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
            if not chunks:
                # Try to extract text directly from document if no chunks found
                logger.info(f"No chunks found for document {document_id}, extracting text directly")
                from app.services.document_processor import DocumentProcessor
                
                # Get document processor from service container
                from flask import current_app
                document_processor = current_app.services.get('document_processor')
                
                if document_processor:
                    # Extract text and create a single chunk for the entire document
                    text = document_processor._extract_document_text(document)
                    if text and len(text.strip()) > 0:
                        # Create a single chunk for the whole document if text extraction was successful
                        chunk = DocumentChunk(
                            chunk_text=text,
                            chunk_index=0,
                            document_id=document_id
                        )
                        db.session.add(chunk)
                        db.session.commit()
                        chunks = [chunk]
                    else:
                        return [], "Failed to extract text from document"
                else:
                    return [], "No document chunks found and document processor not available"
            
            # Fallback if still no chunks
            if not chunks:
                return [], "Failed to extract text or create chunks for this document"
            
            # Improved chunk selection for diverse questions
            selected_chunks = self._select_diverse_chunks(chunks, count, max_chunks=10)
            
            # Balance question types if mixed
            questions = []
            
            if question_type == 'mixed':
                # Distribute among different question types
                types = ['mcq', 'qa', 'true_false', 'fill_in_blank']
                type_counts = {}
                
                # Distribute evenly
                base_count = count // len(types)
                remainder = count % len(types)
                
                for t in types:
                    type_counts[t] = base_count
                    if remainder > 0:
                        type_counts[t] += 1
                        remainder -= 1
                
                # Generate each type with balanced difficulties
                for qtype, qcount in type_counts.items():
                    if qcount <= 0:
                        continue
                    
                    # Distribute questions across difficulty levels
                    difficulty_counts = self._distribute_by_difficulty(qcount, difficulty_levels)    
                    for difficulty, diff_count in difficulty_counts.items():
                        batch = self._generate_questions_batch(selected_chunks, user_id, qtype, diff_count, difficulty)
                        questions.extend(batch)
            else:
                # Generate single type with balanced difficulties
                difficulty_counts = self._distribute_by_difficulty(count, difficulty_levels)
                for difficulty, diff_count in difficulty_counts.items():
                    batch = self._generate_questions_batch(selected_chunks, user_id, question_type, diff_count, difficulty)
                    questions.extend(batch)
            
            # Check if any questions were generated
            if not questions:
                return [], "Failed to generate any questions from the document content"
            
            # Return generated questions
            return [q.to_dict() for q in questions], None
            
        except Exception as e:
            logger.exception(f"Error generating questions: {str(e)}")
            return [], str(e)
    
    def _distribute_by_difficulty(self, total_count: int, difficulty_levels: List[str]) -> Dict[str, int]:
        """Distribute question counts across specified difficulty levels"""
        if not difficulty_levels:
            return {"medium": total_count}
            
        result = {}
        base_count = total_count // len(difficulty_levels)
        remainder = total_count % len(difficulty_levels)
        
        for level in difficulty_levels:
            result[level] = base_count
            if remainder > 0:
                result[level] += 1
                remainder -= 1
                
        return result
    
    def _generate_questions_batch(self, chunks, user_id, question_type, count, target_difficulty=None):
        """Generate a batch of questions of a specific type and difficulty with caching"""
        questions = []
        chunks_used = set()
        
        # Try using each chunk
        for chunk in chunks:
            # Skip if we've generated enough questions
            if len(questions) >= count:
                break
                
            # Generate a question based on type
            question_data = None
            context = chunk.chunk_text
            context_hash = self._get_content_hash(context)
            
            # Check if we've already used this content hash
            if context_hash in chunks_used:
                continue
                
            # Check if cached
            cached = False
            if context_hash in self.question_cache and question_type in self.question_cache[context_hash]:
                question_data = self.question_cache[context_hash][question_type]
                cached = True
                logger.info(f"Using cached {question_type} question")
            
            # Generate if not cached
            if not cached:
                if question_type == 'mcq':
                    question_data = self.generate_mcq(context)
                elif question_type == 'qa':
                    question_data = self.generate_qa(context)
                elif question_type == 'true_false':
                    question_data = self.generate_true_false(context)
                elif question_type == 'fill_in_blank':
                    question_data = self.generate_fill_in_blank(context)
            
            # Skip if generation failed
            if not question_data or 'question' not in question_data:
                continue
                
            # Skip if difficulty doesn't match target (if specified)
            question_difficulty = question_data.get('difficulty', 'medium')
            if target_difficulty and question_difficulty != target_difficulty:
                # Try to adjust difficulty if possible
                if 'question' in question_data and 'answer' in question_data:
                    question_data['difficulty'] = target_difficulty
            
            # Create question object
            try:
                # Create options JSON for appropriate question types
                options_json = None
                if question_type == 'mcq' and 'options' in question_data:
                    options_json = json.dumps(question_data['options'])
                elif question_type == 'fill_in_blank' and 'options' in question_data:
                    options_json = json.dumps(question_data['options'])
                
                # Create the question with specified difficulty
                question = Question(
                    question_text=question_data['question'],
                    question_type=question_type,
                    options=options_json,
                    answer=question_data.get('answer', ''),
                    document_id=chunk.document_id,
                    user_id=user_id,
                    difficulty=question_data.get('difficulty', 'medium') if not target_difficulty else target_difficulty,
                    content_hash=context_hash
                )
                
                db.session.add(question)
                db.session.commit()
                
                questions.append(question)
                chunks_used.add(context_hash)
                
                # Add delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.exception(f"Error saving question: {str(e)}")
                db.session.rollback()
        
        return questions
    
    def _select_diverse_chunks(self, chunks: List[DocumentChunk], desired_count: int, max_chunks: int) -> List[DocumentChunk]:
        """Select diverse chunks from document for question generation"""
        if not chunks:
            return []
            
        # If few chunks available, return all of them
        if len(chunks) <= desired_count:
            return chunks
            
        # Sort chunks by order
        sorted_chunks = sorted(chunks, key=lambda x: x.chunk_index)
        total_chunks = len(sorted_chunks)
        
        # Divide document into sections and select chunks from each section
        num_sections = min(desired_count, total_chunks)
        section_size = total_chunks / num_sections
        
        selected_chunks = []
        for i in range(num_sections):
            # Calculate section indices
            section_start = int(i * section_size)
            section_end = int((i + 1) * section_size)
            
            # Select chunk from this section
            if section_start < section_end and section_start < total_chunks:
                # Add some randomness when selecting from section
                section_chunks = sorted_chunks[section_start:min(section_end, total_chunks)]
                if section_chunks:
                    selected_chunks.append(random.choice(section_chunks))
        
        # If not enough chunks, add more random ones
        remaining = desired_count - len(selected_chunks)
        if remaining > 0 and total_chunks > len(selected_chunks):
            remaining_chunks = [c for c in sorted_chunks if c not in selected_chunks]
            random.shuffle(remaining_chunks)
            selected_chunks.extend(remaining_chunks[:remaining])
        
        # Limit to max chunks and shuffle the result
        result = selected_chunks[:max_chunks]
        random.shuffle(result)
        
        return result
        
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
                
        elif question.question_type == 'true_false':
            # For True/False, direct comparison
            try:
                is_correct = user_answer.lower() == correct_answer.lower()
                return {
                    'is_correct': is_correct,
                    'correct_answer': correct_answer,
                    'score': 1 if is_correct else 0
                }
            except:
                return {'error': 'Error evaluating True/False answer'}
                
        elif question.question_type == 'fill_in_blank':
            # For fill-in-the-blank, compare with some flexibility
            try:
                # Clean up answers for comparison (lowercase, remove punctuation)
                clean_user = re.sub(r'[^\w\s]', '', user_answer.lower()).strip()
                clean_correct = re.sub(r'[^\w\s]', '', correct_answer.lower()).strip()
                
                # Direct match
                if clean_user == clean_correct:
                    is_correct = True
                    score = 1
                else:
                    # Calculate similarity for partial credit
                    similarity = self._simple_similarity(clean_user, clean_correct)
                    is_correct = similarity > 0.8  # High threshold for correctness
                    score = round(similarity, 2)  # Score as percentage
                
                return {
                    'is_correct': is_correct,
                    'correct_answer': correct_answer,
                    'score': score,
                    'similarity': similarity if 'similarity' in locals() else 1.0
                }
            except Exception as e:
                logger.exception(f"Error evaluating fill-in-blank answer: {str(e)}")
                return {'error': 'Error evaluating fill-in-blank answer'}
        
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
        # Improved similarity calculation handling different types of input
        if not str1 or not str2:
            return 0.0
            
        # For very short answers, try exact matching or substring
        if len(str1) < 5 or len(str2) < 5:
            if str1 == str2:
                return 1.0
            if str1 in str2 or str2 in str1:
                return 0.8
        
        # For longer text, use word-based comparison
        words1 = set(str1.lower().split())
        words2 = set(str2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        # Check word overlap
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        jaccard = len(intersection) / len(union)
        
        # Also consider word order with bigrams
        bigrams1 = self._get_bigrams(str1.lower())
        bigrams2 = self._get_bigrams(str2.lower())
        
        if bigrams1 and bigrams2:
            bi_intersection = set(bigrams1) & set(bigrams2)
            bi_union = set(bigrams1) | set(bigrams2)
            bigram_sim = len(bi_intersection) / max(1, len(bi_union))
            # Combine scores
            return (jaccard + bigram_sim) / 2
        
        return jaccard
    
    def _get_bigrams(self, text: str) -> List[str]:
        """Get bigrams from text"""
        words = text.split()
        if len(words) < 2:
            return []
        return [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]