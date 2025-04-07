# app/services/document_processor.py - Improved Document Processor

import os
import uuid
import re
import logging
import requests
from werkzeug.utils import secure_filename

from app import db
from app.models.document import Document, DocumentChunk

# Set up logging
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing uploaded documents"""
    
    def __init__(self, upload_folder, allowed_extensions):
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions
        
        # Create upload folder if it doesn't exist
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def allowed_file(self, filename):
        """Check if the file type is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_file(self, file, user_id):
        """Save uploaded file and create document record"""
        if not file or not self.allowed_file(file.filename):
            return None, "Invalid file or file type not allowed"
        
        try:
            # Generate a secure filename to prevent path traversal attacks
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Check file size before saving
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            
            if file_size > 5 * 1024 * 1024:  # Limit to 5MB
                return None, "File too large. Maximum file size is 5MB."
            
            # Save the file
            file.save(file_path)
            logger.info(f"File saved to {file_path}")
            
            # Create document record
            document = Document(
                filename=unique_filename,
                original_filename=original_filename,
                file_type=file_extension,
                file_size=file_size,
                file_path=file_path,
                user_id=user_id
            )
            
            db.session.add(document)
            db.session.commit()
            logger.info(f"Document record created with ID {document.id}")
            
            # Extract and store text chunks
            success, error = self.process_document_text(document)
            if not success:
                logger.error(f"Error processing document: {error}")
                return None, error
            
            return document, None
        except Exception as e:
            logger.exception("Error in save_file")
            db.session.rollback()
            return None, str(e)
    
    def process_document_text(self, document):
        """Extract text from document and create chunks"""
        file_path = document.file_path
        file_type = document.file_type
        
        try:
            logger.info(f"Processing document: {document.id}, type: {file_type}")
            
            # Extract text based on file type
            if file_type == 'pdf':
                try:
                    import PyPDF2
                    text = self._extract_text_from_pdf(file_path)
                except ImportError:
                    logger.warning("PyPDF2 not available, using basic text extraction")
                    text = self._extract_text_basic(file_path)
            elif file_type == 'docx':
                try:
                    import docx
                    text = self._extract_text_from_docx(file_path)
                except ImportError:
                    logger.warning("python-docx not available, using basic text extraction")
                    text = self._extract_text_basic(file_path)
            elif file_type == 'txt':
                text = self._extract_text_from_txt(file_path)
            else:
                return False, f"Unsupported file type: {file_type}"
            
            text_length = len(text)
            logger.info(f"Text extracted, length: {text_length} characters")
            
            # Truncate very long texts to prevent memory issues
            if text_length > 50000:
                logger.warning(f"Text too long ({text_length} chars), truncating to 50000")
                text = text[:50000]
                text_length = 50000
            
            # Improved chunking with better overlap handling
            chunk_size = 1000
            overlap = 100
            
            # HARD LIMIT on number of chunks
            MAX_CHUNKS = 50
            
            # Delete any existing chunks for this document
            existing_chunks = DocumentChunk.query.filter_by(document_id=document.id).all()
            for chunk in existing_chunks:
                db.session.delete(chunk)
            db.session.commit()
            
            # Create chunks
            start = 0
            chunk_index = 0
            
            while start < text_length and chunk_index < MAX_CHUNKS:
                # Calculate chunk end position
                end = min(start + chunk_size, text_length)
                
                # Try to find a good break point (sentence end)
                if end < text_length:
                    # Look for sentence endings (.!?) with possible trailing spaces
                    match = re.search(r'[.!?]\s*', text[max(end-50, start):end])
                    if match:
                        end = max(end-50, start) + match.end()
                
                # Extract chunk
                chunk_text = text[start:end].strip()
                
                # Skip empty chunks
                if not chunk_text:
                    start = end
                    continue
                
                # Create and save chunk
                doc_chunk = DocumentChunk(
                    chunk_text=chunk_text,
                    chunk_index=chunk_index,
                    document_id=document.id
                )
                db.session.add(doc_chunk)
                
                # Commit each chunk immediately
                db.session.commit()
                logger.info(f"Saved chunk {chunk_index}, length: {len(chunk_text)}")
                
                # Move to next chunk with proper overlap
                start = end - overlap
                chunk_index += 1
            
            if chunk_index >= MAX_CHUNKS and start < text_length:
                logger.warning(f"Reached maximum chunk limit ({MAX_CHUNKS}), truncating document")
            
            return True, None
        
        except Exception as e:
            logger.exception("Error in process_document_text")
            db.session.rollback()
            return False, str(e)
    
    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF file with safety limits"""
        import PyPDF2
        text = ""
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                # Limit to 10 pages only
                pages_to_process = min(len(pdf_reader.pages), 10)
                logger.info(f"Processing {pages_to_process} pages from PDF")
                
                for i in range(pages_to_process):
                    try:
                        page = pdf_reader.pages[i]
                        page_text = page.extract_text()
                        # Add page number for reference
                        text += f"\n--- Page {i+1} ---\n"
                        text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {i}: {e}")
                    
            return text
        except Exception as e:
            logger.exception("Error extracting text from PDF")
            # Return empty string to fail gracefully
            return ""
    
    def _extract_text_from_docx(self, file_path):
        """Extract text from DOCX file with safety limits"""
        import docx
        try:
            doc = docx.Document(file_path)
            paragraphs = doc.paragraphs
            
            # Limit number of paragraphs for safety
            max_paragraphs = 100
            if len(paragraphs) > max_paragraphs:
                logger.warning(f"Limiting document to {max_paragraphs} paragraphs (was {len(paragraphs)})")
                paragraphs = paragraphs[:max_paragraphs]
                
            text = ""
            for paragraph in paragraphs:
                text += paragraph.text + "\n"
                
            return text
        except Exception as e:
            logger.exception("Error extracting text from DOCX")
            # Return empty string to fail gracefully
            return ""
    
    def _extract_text_from_txt(self, file_path):
        """Extract text from TXT file with safety limits"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Read up to 50000 chars for safety
                text = f.read(50000)
            return text
        except Exception as e:
            logger.exception("Error extracting text from TXT")
            # Return empty string to fail gracefully
            return ""
    
    def _extract_text_basic(self, file_path):
        """Fallback text extraction - try to read as text with various encodings"""
        encodings = ['utf-8', 'latin-1', 'ascii']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    # Read up to 50000 chars for safety
                    return f.read(50000)
            except:
                continue
        return ""
    
    def get_document_text(self, document_id):
        """Get text from document chunks"""
        document = Document.query.get(document_id)
        if not document:
            return None, "Document not found"
        
        document.update_last_accessed()
        
        try:
            # Get chunks
            chunks = DocumentChunk.query.filter_by(document_id=document_id).order_by(DocumentChunk.chunk_index).all()
            
            if not chunks:
                # Fallback to extraction if no chunks
                return self._extract_document_text(document), None
            
            # Combine chunks - limit number of chunks to prevent memory issues
            MAX_CHUNKS_TO_COMBINE = 50
            if len(chunks) > MAX_CHUNKS_TO_COMBINE:
                logger.warning(f"Limiting to {MAX_CHUNKS_TO_COMBINE} chunks for text retrieval (was {len(chunks)})")
                chunks = chunks[:MAX_CHUNKS_TO_COMBINE]
            
            # Combine chunks
            text = "\n".join(chunk.chunk_text for chunk in chunks)
            return text, None
            
        except Exception as e:
            logger.exception(f"Error getting document text: {e}")
            return None, str(e)
    
    def _extract_document_text(self, document):
        """Fallback to extract text directly from file"""
        try:
            file_type = document.file_type
            file_path = document.file_path
            
            if file_type == 'pdf':
                try:
                    import PyPDF2
                    return self._extract_text_from_pdf(file_path)
                except ImportError:
                    return self._extract_text_basic(file_path)
                    
            elif file_type == 'docx':
                try:
                    import docx
                    return self._extract_text_from_docx(file_path)
                except ImportError:
                    return self._extract_text_basic(file_path)
                    
            elif file_type == 'txt':
                return self._extract_text_from_txt(file_path)
                
            else:
                return "Unsupported file type"
                
        except Exception as e:
            logger.exception(f"Error in _extract_document_text: {e}")
            return "Error extracting text"
    
    def delete_document(self, document_id, user_id):
        """Delete document and its file"""
        document = Document.query.filter_by(id=document_id, user_id=user_id).first()
        if not document:
            return False, "Document not found or you don't have permission"
        
        try:
            # Delete the file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete the document record and associated chunks
            chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
            for chunk in chunks:
                db.session.delete(chunk)
                
            db.session.delete(document)
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def summarize_document(self, document_id):
        """Summarize a document using Claude API"""
        document = Document.query.get(document_id)
        if not document:
            return None, "Document not found"
        
        try:
            # Get document text
            text, error = self.get_document_text(document_id)
            if error:
                return None, f"Error getting document text: {error}"
            
            # Use Claude API to summarize
            from flask import current_app
            api_key = current_app.config['ANTHROPIC_API_KEY']
            
            if not api_key:
                return None, "API key not configured"
            
            # Maximum length for text to summarize
            max_length = 10000
            if len(text) > max_length:
                logger.warning(f"Text too long ({len(text)} chars) for summarization, truncating to {max_length}")
                text = text[:max_length]
            
            # API endpoint and headers
            api_url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # Create prompt for document summarization
            messages = [
                {
                    "role": "user",
                    "content": f"""Please provide a concise but comprehensive summary of the following document.
                    Focus on the main points, key arguments, and important conclusions.
                    Organize the summary with clear headings and bullet points where appropriate.
                    
                    DOCUMENT TO SUMMARIZE:
                    {text}
                    """
                }
            ]
            
            # Prepare API request
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1500,
                "temperature": 0.3,
                "messages": messages
            }
            
            # Make API call
            logger.info(f"Sending summarization request to Claude API for document {document_id}")
            response = requests.post(api_url, headers=headers, json=payload)
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return None, f"Error from Claude API: {response.status_code}"
            
            # Extract summary
            result = response.json()
            if 'content' in result and len(result['content']) > 0:
                summary = result['content'][0]['text'].strip()
                logger.info(f"Successfully summarized document {document_id}")
                return summary, None
            else:
                logger.error("Invalid response from Claude API")
                return None, "Failed to generate summary"
            
        except Exception as e:
            logger.exception(f"Error in summarize_document: {str(e)}")
            return None, str(e)