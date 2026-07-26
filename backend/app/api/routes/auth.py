from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.auth import get_user_id_manager

router = APIRouter(tags=["auth"])


class UserIDResponse(BaseModel):
    user_id: str
    expires_in_seconds: int = 30 * 24 * 60 * 60  # 30 days


class VerifyUserIDRequest(BaseModel):
    user_id: str


class VerifyUserIDResponse(BaseModel):
    valid: bool
    uuid: str | None = None


@router.post("/auth/generate-user-id")
def generate_user_id():
    """
    Generate a new HMAC-signed user ID.
    Client should store this in localStorage and send with all requests.
    """
    manager = get_user_id_manager()
    token = manager.generate_user_id()
    return UserIDResponse(user_id=token)


@router.post("/auth/verify-user-id")
def verify_user_id(request: VerifyUserIDRequest):
    """
    Verify a user ID token. Returns the embedded UUID if valid.
    """
    manager = get_user_id_manager()
    uuid = manager.verify_user_id(request.user_id)
    
    if uuid is None:
        raise HTTPException(status_code=401, detail="Invalid or expired user ID")
    
    return VerifyUserIDResponse(valid=True, uuid=uuid)
