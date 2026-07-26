from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/session", tags=["Session"])


@router.get("/")
def get_session(user_id: str = Depends(get_current_user)):
    """
    Get the authenticated user's session information.
    
    Requires X-User-ID header with valid authenticated user ID.
    
    Returns:
        - user_id: The authenticated user's UUID
        - session_active: Whether the session is currently active
    """
    return {
        "user_id": user_id,
        "session_active": True
    }