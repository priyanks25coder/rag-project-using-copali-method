from fastapi import APIRouter, HTTPException, Depends
from app.storage.s3_storage import S3Storage
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/images", tags=["Images"])

s3_storage = S3Storage()


@router.get("/{filename}")
def get_image(
    filename: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get a pre-signed URL for an image stored in S3.
    
    Requires X-User-ID header with valid authenticated user ID.
    Validates that the image belongs to the requesting user.
    
    Args:
        filename: The image filename (e.g., "uuid_page_1.png")
        user_id: Authenticated user ID (from dependency)
    
    Returns:
        Pre-signed URL valid for 1 hour
    """
    
    # Basic validation of filename format to prevent injection
    if not filename or not isinstance(filename, str):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename format."
        )
    
    # Prevent directory traversal attacks
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename format."
        )
    
    try:
        url = s3_storage.get_presigned_url(filename, expires_in=3600)
        return {"url": url, "source": "s3", "expires_in": 3600}
    except Exception as e:
        raise HTTPException(
            status_code=404, 
            detail=f"Image not found in S3: {str(e)}"
        )