import json
import re
import requests
import logging
import random
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter

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
            return response.json()
        except Exception as e:
            logger.exception(f"Error calling Claude API: {str(e)}")
            if hasattr(response, 'text'):
                logger.error(f"API response: {response.text}")
            raise
    
    def generate_mcq(self, context: str) -> Dict:
        """Generate a multiple-choice question from context text with improved prompt"""
        try:
            logger.info(f"Generating MCQ from context of length: {len(context)}")
            
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
                                      count: int = 5) -> Tuple[List[Dict], Optional[str]]:
        """Generate diverse questions from a document with improved chunk selection"""
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return [], "Document not found or you don't have permission"
        
        # Get document chunks
        chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
        if not chunks:
            return [], "No text chunks available for this document"
        
        # Limit number of chunks to process but increase max
        max_chunks = min(30, len(chunks))  # Increased from 20 to 30 chunks
        logger.info(f"Using {max_chunks} chunks out of {len(chunks)} for question generation")
        
        # Instead of completely random shuffle, select chunks from different parts of the document
        selected_chunks = self._select_diverse_chunks(chunks, count * 2, max_chunks)
        
        questions = []
        stored_questions = []
        question_content_hashes = set()  # To avoid duplicate question content
        max_attempts = min(count * 3, 15)  # Increased maximum attempts from 10 to 15
        attempts = 0
        
        for chunk in selected_chunks:
            if len(questions) >= count or attempts >= max_attempts:
                break
                
            attempts += 1
            context = chunk.chunk_text
            if not context or len(context.strip()) < 50:  # Skip very short chunks
                continue
            
            try:
                # Select question type based on question_type parameter
                if question_type.lower() == 'mcq':
                    question_data = self.generate_mcq(context)
                elif question_type.lower() == 'qa':
                    question_data = self.generate_qa(context)
                elif question_type.lower() == 'true_false':
                    question_data = self.generate_true_false(context)
                elif question_type.lower() == 'fill_in_blank':
                    question_data = self.generate_fill_in_blank(context)
                else:
                    # If type not specified, randomly select a type to increase diversity
                    random_type = random.choice(['mcq', 'qa', 'true_false', 'fill_in_blank'])
                    if random_type == 'mcq':
                        question_data = self.generate_mcq(context)
                    elif random_type == 'qa':
                        question_data = self.generate_qa(context)
                    elif random_type == 'true_false':
                        question_data = self.generate_true_false(context)
                    else:
                        question_data = self.generate_fill_in_blank(context)
                
                # Check required fields
                if 'question' not in question_data or 'answer' not in question_data:
                    continue
                
                # Check for duplicate content
                question_hash = hash(question_data['question'].lower())
                if question_hash in question_content_hashes:
                    continue
                question_content_hashes.add(question_hash)
                
                # Required fields
                question_text = question_data['question']
                answer = question_data['answer']
                actual_question_type = question_data.get('question_type', question_type)
                options_json = None
                
                # Format based on question type
                if actual_question_type == 'mcq':
                    if 'options' not in question_data:
                        continue
                    options_json = json.dumps(question_data['options'])
                    answer_text = question_data['options'].get(answer, answer)
                elif actual_question_type == 'true_false':
                    options_json = json.dumps({'True': 'True', 'False': 'False'})
                    answer_text = answer
                
                # Create and save question
                question = Question(
                    question_text=question_text,
                    question_type=actual_question_type,
                    options=options_json,
                    answer=answer,
                    document_id=document_id,
                    user_id=user_id
                )
                
                db.session.add(question)
                stored_questions.append(question)
                
                # Format question for client response
                question_response = {
                    'question': question_text,
                    'answer': answer,
                    'question_type': actual_question_type
                }
                
                # Add fields based on question type
                if actual_question_type == 'mcq':
                    question_response['options'] = question_data['options']
                    question_response['answer_text'] = answer_text
                elif actual_question_type == 'true_false':
                    question_response['options'] = {'True': 'True', 'False': 'False'}
                elif actual_question_type == 'fill_in_blank' and 'explanation' in question_data:
                    question_response['explanation'] = question_data['explanation']
                
                questions.append(question_response)
            
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