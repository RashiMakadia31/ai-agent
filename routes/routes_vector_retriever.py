from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
import json
import os

# Initialize router and logger for this API module
router = APIRouter()
logger = logging.getLogger(__name__)

# Constants for model and data paths (can be configured via environment or defaults)
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
INDEX_PATH = "vector_db/code_snippets.index"
SNIPPETS_PATH = "vector_db/snippets.json"

# Initialize embedding model and load FAISS index + snippet metadata
try:
    model = SentenceTransformer(MODEL_NAME)  # Load pre-trained sentence transformer model
    index = faiss.read_index(INDEX_PATH)      # Load FAISS index from file
    with open(SNIPPETS_PATH, "r") as f:
        snippets = json.load(f)               # Load snippet ID -> code mapping
    logger.info("Vector index and snippets loaded successfully.")
except Exception as e:
    logger.error(f"Startup loading error: {e}")
    # If loading fails, stop app from starting (critical failure)
    raise RuntimeError("Failed to initialize vector retrieval service.")

# Define request structure: expects a 'query' string from client
class RetrievalRequest(BaseModel):
    query: str  # Natural language or code query

# Define response structure: returns best matching snippet and its distance
class RetrievalResponse(BaseModel):
    snippet: str   # Code snippet content
    distance: float  # FAISS distance metric (lower = better match)

# Main API route for snippet retrieval
@router.post("/retrieve-snippet", response_model=RetrievalResponse)
async def retrieve_code_snippet(request: RetrievalRequest):
    """
    Given a natural language or code query, retrieves the most relevant code snippet
    using embedding search via FAISS.
    """
    try:
        # Generate query embedding using the transformer model
        query_embedding = model.encode([request.query])
        
        # Search FAISS index for the closest match (k=1 = best match only)
        D, I = index.search(np.array(query_embedding), k=1)

        # Check if a valid match was found
        if I is not None and len(I[0]) > 0:
            snippet_id = str(I[0][0])
            
            # Retrieve the matched snippet from the loaded metadata
            if snippet_id in snippets:
                return RetrievalResponse(
                    snippet=snippets[snippet_id],
                    distance=float(D[0][0])
                )
            else:
                # Edge case: index returned ID not present in snippets JSON
                logger.warning(f"Snippet ID {snippet_id} not found in snippet data.")
                raise HTTPException(status_code=404, detail="Snippet not found.")
        else:
            # No valid match found in FAISS index
            logger.warning("No valid match found in FAISS index.")
            raise HTTPException(status_code=404, detail="No relevant snippet found.")
    
    except Exception as e:
        # Handle unexpected errors during retrieval
        logger.error(f"Vector retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve code snippet")
