import numpy as np
import faiss
import requests
import pickle
import os
import logging
import time
import hashlib
from functools import lru_cache
from typing import List, Dict, Tuple, Optional

from app import db
from app.models.document import Document, DocumentChunk

# Set up logging
logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Service for managing document embeddings and semantic search using Claude API"""
    
    def __init__(self, api_key, index_directory='app/static/indices', cache_size=100):
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
            
        # Initialize embedding cache
        self._text_hash_cache = {}
        self.get_embedding_cached = lru_cache(maxsize=cache_size)(self._get_single_embedding)
        
        logger.info(f"Initialized EmbeddingsService with Claude API and cache size {cache_size}")
    
    def _text_to_hash(self, text: str) -> str:
        """Convert text to a hash for caching"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
        
    def _get_single_embedding(self, text_hash: str) -> np.ndarray:
        """Get embedding for a single text by hash (for caching)"""
        if text_hash not in self._text_hash_cache:
            return np.array([])
        
        text = self._text_hash_cache[text_hash]
        try:
            # Claude Embeddings API call for a single text
            payload = {
                "model": "claude-3-opus-20240229", 
                "input": [text],
                "encoding_format": "float"
            }
            
            response = requests.post(
                self.embeddings_api_url, 
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            # Extract embedding from response
            result = response.json()
            if 'data' not in result or not result['data']:
                logger.error(f"Invalid response format: {result}")
                return np.array([])
                
            return np.array(result['data'][0]['embedding'])
            
        except Exception as e:
            logger.exception(f"Error getting single embedding: {str(e)}")
            return np.array([])
    
    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using Claude API with caching"""
        if not texts:
            return np.array([])
            
        try:
            # Process each text with cache
            result_embeddings = []
            uncached_texts = []
            uncached_indices = []
            
            # Check cache first
            for i, text in enumerate(texts):
                text_hash = self._text_to_hash(text)
                self._text_hash_cache[text_hash] = text  # Store mapping of hash to text
                
                cached_embedding = self.get_embedding_cached(text_hash)
                if cached_embedding.size > 0:
                    result_embeddings.append((i, cached_embedding))
                    logger.debug(f"Cache hit for text at index {i}")
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
                    logger.debug(f"Cache miss for text at index {i}")
            
            # For uncached texts, process in batches
            if uncached_texts:
                logger.info(f"Processing {len(uncached_texts)} uncached texts in batches")
                batch_size = 5  # Small batch size
                batch_embeddings = []
                
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i+batch_size]
                    logger.info(f"Getting embeddings for batch {i//batch_size + 1}/{(len(uncached_texts)-1)//batch_size + 1}")
                    
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
                                
                            # Add embeddings to batch results
                            embeddings = [np.array(item['embedding']) for item in result['data']]
                            batch_embeddings.extend(embeddings)
                            
                            # Update cache for these embeddings
                            for j, emb in enumerate(embeddings):
                                original_idx = i + j
                                if original_idx < len(uncached_texts):
                                    text_hash = self._text_to_hash(uncached_texts[original_idx])
                                    self.get_embedding_cached.cache_clear()  # Clear cache to update
                                    self.get_embedding_cached(text_hash)  # Call once to cache
                            
                            # Add delay between API calls
                            if i + batch_size < len(uncached_texts):
                                time.sleep(1)  # 1 second delay between batches
                                
                            break  # Success, exit retry loop
                            
                        except Exception as e:
                            logger.warning(f"Embedding attempt {attempt+1} failed: {str(e)}")
                            if attempt < max_retries - 1:
                                time.sleep(2)  # Wait before retry
                            else:
                                logger.error(f"Failed to embed batch after {max_retries} attempts")
                                # Fill with empty arrays as placeholder for failed embeddings
                                batch_embeddings.extend([np.array([]) for _ in range(len(batch))])
                
                # Combine batch results with their original indices
                for i, idx in enumerate(uncached_indices):
                    if i < len(batch_embeddings) and batch_embeddings[i].size > 0:
                        result_embeddings.append((idx, batch_embeddings[i]))
            
            # Sort by original index and combine
            result_embeddings.sort(key=lambda x: x[0])
            
            # Check if we got any valid embeddings
            if not result_embeddings:
                return np.array([])
                
            # Verify all embeddings have the same dimension
            first_dim = result_embeddings[0][1].shape[0]
            all_embeddings = np.zeros((len(texts), first_dim))
            
            # Fill in the embeddings we have
            for idx, emb in result_embeddings:
                all_embeddings[idx] = emb
                
            return all_embeddings
            
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