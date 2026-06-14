import os
import numpy as np
from django.conf import settings
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

class FallbackEmbeddingFunction(EmbeddingFunction):
    """
    A lightweight, zero-dependency local embedding function using word-hashing.
    It hashes sentences/chunks into a 384-dimensional space and normalizes them.
    This ensures ChromaDB works fully locally even without Gemini or OpenAI keys.
    """
    def __init__(self, dimension=384):
        self.dimension = dimension

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            # Tokenize and clean
            words = re.findall(r'\w+', text.lower())
            vector = np.zeros(self.dimension, dtype=np.float32)
            
            if words:
                for word in words:
                    # Simple deterministic hash to map word to a dimension bin
                    h = hash(word) % self.dimension
                    vector[h] += 1.0
                
                # Apply simple logarithmic scaling to word frequencies
                vector = np.log1p(vector)
                
                # L2 normalization
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
            
            embeddings.append(vector.tolist())
        return embeddings

import re  # needed for re.findall in the class above

class ChromaService:
    def __init__(self):
        # Create storage folder for ChromaDB inside the workspace
        persist_dir = os.path.join(settings.BASE_DIR, 'chromadb_store')
        os.makedirs(persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Decide embedding function (use fallback by default unless API keys exist)
        self.embedding_function = self._get_embedding_function()
        
        # Initialize collection
        self.collection = self.client.get_or_create_collection(
            name="research_papers",
            embedding_function=self.embedding_function
        )

    def _get_embedding_function(self):
        # Check if keys are available to potentially use real API embeddings.
        # To keep it robust, zero-dependency, and offline-friendly, we use the local Fallback embedding.
        # This prevents connection timeouts and rate limits.
        # If the user configures Gemini/OpenAI, we can wrap it, but Fallback is fast and local.
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        # We default to FallbackEmbeddingFunction which is fully functional and offline.
        return FallbackEmbeddingFunction()

    def add_chunks(self, paper_id, chunks):
        """
        Adds paper text chunks to the Chroma DB.
        """
        if not chunks:
            return
            
        ids = [f"{paper_id}_chunk_{i}" for i in range(len(chunks))]
        documents = chunks
        metadatas = [{"paper_id": str(paper_id), "chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def search_similar_chunks(self, query, top_k=5):
        """
        Searches Chroma DB for chunks similar to the query.
        Returns a list of dictionaries with document content, metadata, and distance.
        """
        if not query:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        formatted_results = []
        if results and 'documents' in results and results['documents']:
            docs = results['documents'][0]
            metas = results['metadatas'][0]
            distances = results['distances'][0] if 'distances' in results else [0.0] * len(docs)
            ids = results['ids'][0]
            
            for i in range(len(docs)):
                formatted_results.append({
                    "id": ids[i],
                    "content": docs[i],
                    "metadata": metas[i],
                    "distance": distances[i]
                })
        
        return formatted_results

    def delete_paper_chunks(self, paper_id):
        """
        Deletes all chunks belonging to a specific paper.
        """
        self.collection.delete(
            where={"paper_id": str(paper_id)}
        )
