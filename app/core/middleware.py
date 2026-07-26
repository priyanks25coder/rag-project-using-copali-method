from fastapi import Request, HTTPException
from app.core.auth import get_user_id_manager
from app.config.settings import ENVIRONMENT
import logging

logger = logging.getLogger(__name__)


async def verify_user_id_middleware(request: Request, call_next):
    """
    Middleware that extracts and verifies the user ID from X-User-ID header.
    Skips verification for auth routes (they don't need a user ID yet).
    In production, docs are protected. In development, they're publicly accessible.
    """
    # Skip verification for auth routes (always needed to generate first token)
    if request.url.path.startswith("/api/v1/auth/"):
        return await call_next(request)
    
    # Skip verification for docs/openapi only in development
    if ENVIRONMENT == "development" and request.url.path in ["/docs", "/openapi.json", "/", "/redoc"]:
        return await call_next(request)
    
    # Get user ID from header
    user_id_token = request.headers.get("X-User-ID")
    
    if not user_id_token:
        raise HTTPException(
            status_code=401,
            detail="Missing X-User-ID header. Please generate a user ID first."
        )
    
    # Verify the token
    manager = get_user_id_manager()
    user_uuid = manager.verify_user_id(user_id_token)
    
    if not user_uuid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired user ID. Please generate a new one."
        )
    
    # Store verified user ID in request state for use in route handlers
    request.state.user_id = user_uuid
    request.state.user_id_token = user_id_token
    
    logger.debug(f"Verified user ID: {user_uuid}")
    
    response = await call_next(request)
    return response
