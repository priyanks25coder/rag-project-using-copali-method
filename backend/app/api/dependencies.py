from fastapi import Request, HTTPException, Depends
from app.db.qdrant_vectorstore import QdrantVectorStoreConnection

def get_qdrant(request: Request) -> QdrantVectorStoreConnection:
    """
    Dependency to get the Qdrant connection stored in app.state.
    Created once at startup, reused for all requests.
    """
    if not hasattr(request.app.state, "qdrant"):
        raise HTTPException(
            status_code=500,
            detail="Qdrant connection not initialized.",
        )
    return request.app.state.qdrant


def get_current_user(request: Request) -> str:
    """
    Dependency to get the authenticated user ID from request state.
    This extracts the user_id that was verified by middleware.
    
    Returns:
        str: The authenticated user's UUID
        
    Raises:
        HTTPException: If user_id is not found in request state (401)
    """
    if not hasattr(request.state, "user_id") or not request.state.user_id:
        raise HTTPException(
            status_code=401,
            detail="User authentication required. Please send a valid X-User-ID header."
        )
    
    return request.state.user_id