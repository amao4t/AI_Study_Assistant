import numpy as np
import faiss
import requests
import pickle
import os
import logging
import time
from typing import List, Dict, Tuple, Optional

from app import db
from app.models.document import Document, DocumentChunk

# Set up logging
logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service for managing document embeddings and semantic search using Claude API"""
    
    def __init__(self, api_key, index_directory='app/static/indices'):
        self.api_key = api_key
        self.index_directory = index_directory
        self.embeddings_api_url = "https://api.anthropic.com/v1/embeddings"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Create indices directory if it doesn't exist
        if not os.path.exists(self.index_directory):
            os.makedirs(self.index_directory)
            
        logger.info("Initialized EmbeddingsService with Claude API")
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using Claude API"""
        if not texts:
            return np.array([])
            
        try:
            # Process in smaller batches to avoid API limitations
            batch_size = 5  # Small batch size
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                logger.info(f"Getting embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                # Add retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Claude Embeddings API call
                        payload = {
                            "model": "claude-3-opus-20240229", 
                            "input": batch,
                            "encoding_format": "float"
                        }
                        
                        response = requests.post(
                            self.embeddings_api_url, 
                            headers=self.headers,
                            json=payload
                        )
                        response.raise_for_status()
                        
                        # Extract embeddings from response
                        result = response.json()
                        if 'data' not in result:
                            logger.error(f"Invalid response format: {result}")
                            raise ValueError("Invalid API response format")
                            
                        batch_embeddings = np.array([item['embedding'] for item in result['data']])
                        all_embeddings.append(batch_embeddings)
                        
                        # Add delay between API calls
                        if i + batch_size < len(texts):
                            time.sleep(1)  # 1 second delay between batches
                            
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        logger.warning(f"Embedding attempt {attempt+1} failed: {str(e)}")
                        if attempt < max_retries - 1:
                            time.sleep(2)  # Wait before retry
                        else:
                            logger.error(f"Failed to embed batch after {max_retries} attempts")
                            raise
                
            if all_embeddings:
                return np.vstack(all_embeddings)
            return np.array([])
            
        except Exception as e:
            logger.exception(f"Error getting embeddings: {str(e)}")
            return np.array([])
    
    def create_document_index(self, document_id: int) -> Tuple[bool, Optional[str]]:
        """Create and save FAISS index for a document"""
        document = Document.query.get(document_id)
        if not document:
            return False, "Document not found"
        
        chunks = DocumentChunk.query.filter_by(document_id=document_id).all()
        if not chunks:
            return False, "No chunks found for document"
        
        try:
            # Limit number of chunks to process
            max_chunks = 20  # Process only first 20 chunks for safety
            if len(chunks) > max_chunks:
                logger.warning(f"Limiting to {max_chunks} chunks (was {len(chunks)})")
                chunks = chunks[:max_chunks]
            
            # Get texts from chunks
            texts = [chunk.chunk_text for chunk in chunks]
            chunk_ids = [chunk.id for chunk in chunks]
            
            logger.info(f"Creating index for document {document_id} with {len(texts)} chunks")
            
            # Get embeddings in batches
            embeddings = self.get_embeddings(texts)
            if embeddings.size == 0:
                return False, "Failed to generate embeddings"
            
            # Create and train FAISS index
            dimension = embeddings.shape[1]
            logger.info(f"Created embeddings with dimension {dimension}")
            
            # Use a simple index type that uses less memory
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings)
            
            # Save index and mapping to disk
            index_path = os.path.join(self.index_directory, f"doc_{document_id}_index.faiss")
            mapping_path = os.path.join(self.index_directory, f"doc_{document_id}_mapping.pkl")
            
            faiss.write_index(index, index_path)
            with open(mapping_path, 'wb') as f:
                pickle.dump({'chunk_ids': chunk_ids}, f)
            
            logger.info(f"Index saved to {index_path}")
            
            # Update chunks to mark embeddings as stored
            for chunk in chunks:
                chunk.embedding_stored = True
            
            db.session.commit()
            return True, None
        
        except Exception as e:
            logger.exception(f"Error creating document index: {str(e)}")
            db.session.rollback()
            return False, str(e)
    
    def search_document(self, document_id: int, query: str, top_k: int = 3) -> Tuple[List[Dict], Optional[str]]:
        """Search for relevant chunks in a document using semantic search"""
        document = Document.query.get(document_id)
        if not document:
            return [], "Document not found"
        
        # Check if index exists
        index_path = os.path.join(self.index_directory, f"doc_{document_id}_index.faiss")
        mapping_path = os.path.join(self.index_directory, f"doc_{document_id}_mapping.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(mapping_path):
            logger.info(f"Index not found, creating for document {document_id}")
            success, error = self.create_document_index(document_id)
            if not success:
                return [], error
        
        try:
            # Load index and mapping
            index = faiss.read_index(index_path)
            with open(mapping_path, 'rb') as f:
                mapping = pickle.load(f)
            
            # Get query embedding
            query_embedding = self.get_embeddings([query])
            if query_embedding.size == 0:
                return [], "Failed to generate query embedding"
            
            # Search index
            k = min(top_k, index.ntotal)
            if k == 0:
                return [], "No items in index"
                
            distances, indices = index.search(query_embedding, k)
            
            # Get chunk IDs and texts
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(mapping['chunk_ids']):
                    continue  # Skip invalid indices
                    
                chunk_id = mapping['chunk_ids'][idx]
                chunk = DocumentChunk.query.get(chunk_id)
                if chunk:
                    results.append({
                        'chunk_id': chunk_id,
                        'text': chunk.chunk_text,
                        'score': float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                    })
            
            return results, None
        
        except Exception as e:
            logger.exception(f"Error searching document: {str(e)}")
            return [], str(e)