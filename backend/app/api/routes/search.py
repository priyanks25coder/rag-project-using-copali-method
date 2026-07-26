import gc
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from ...api.dependencies import get_qdrant, get_current_user
from ...core.embeddings.embeddings_model import ColPaliEmbedding
from ...db.qdrant_vectorstore import QdrantVectorStoreConnection

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


class ResultMetadata(BaseModel):
    doc_id: str
    source: str
    page: int
    total_pages: int
    image_path: str
    user_id: Optional[str] = None


class SearchResultItem(BaseModel):
    score: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_current_user),
    qdrant: QdrantVectorStoreConnection = Depends(get_qdrant)
):
    """
    Search documents using ColPali multi-vector embeddings.
    Automatically filters by authenticated user for security.
    
    Requires X-User-ID header with valid authenticated user ID.
    """

    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    embed_model = None

    try:
        # Build filters with authenticated user_id
        # User cannot search other users' documents
        filters = request.filters or {}
        filters["user_id"] = user_id

        # Generate query embedding
        embed_model = ColPaliEmbedding()
        query_embedding = embed_model.embed_texts([request.query])[0]

        print(f"Query embedding shape: {query_embedding.shape}")

        # Search Qdrant with enforced user_id filter
        results = qdrant.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filters=filters,
        )

        results = SearchResponse(
            query=request.query,
            results=[
                SearchResultItem(
                    score=r["score"],
                    metadata=r["metadata"],
                )
                for r in results
            ],
        )

        return results

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )

    finally:
        if embed_model is not None:
            embed_model.cleanup()

        gc.collect()