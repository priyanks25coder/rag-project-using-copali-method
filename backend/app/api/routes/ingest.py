import gc
import fitz
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request

from app.config.settings import (
    MAX_PDF_SIZE_BYTES,
    MAX_PDF_PAGES,
    DOCUMENT_TTL_SECONDS,
)
from ...api.dependencies import get_qdrant, get_current_user
from ...processor.document_ingestion import DocumentIngestion
from ...core.embeddings.embeddings_model import ColPaliEmbedding
from ...core.quota_manager import QuotaManager
from ...db.qdrant_vectorstore import QdrantVectorStoreConnection

router = APIRouter(prefix="/ingest", tags=["Ingestion"])
quota_manager = QuotaManager()

@router.post("/")
async def ingest_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    qdrant: QdrantVectorStoreConnection = Depends(get_qdrant),
):
    """
    Upload and process a PDF document.
    Generates ColPali embeddings and stores them in Qdrant.
    
    Requires X-User-ID header with valid authenticated user ID.
    """

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    file_bytes = await file.read()

    # Check file size
    if len(file_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max allowed size is {MAX_PDF_SIZE_BYTES // (1024*1024)} MB.",
        )

    # Check user quota
    can_upload, reason = quota_manager.can_upload(user_id, len(file_bytes))
    if not can_upload:
        raise HTTPException(
            status_code=429,
            detail=reason,
        )

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        doc.close()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid or corrupted PDF file.",
        )

    if page_count > MAX_PDF_PAGES:
        raise HTTPException(
            status_code=400,
            detail=f"PDF has {page_count} pages. Max allowed is {MAX_PDF_PAGES} pages.",
        )

    # Track upload start
    quota_manager.start_upload(user_id)
    
    di = None
    embed_model = None

    try:
        # Extract pages from PDF bytes
        di = DocumentIngestion(file_bytes=file_bytes, filename=file.filename)
        di.set_document_id()
        img_paths = di.get_pdf_pages()
        images = di.document_pages_img

        print(f"Extracted {len(img_paths)} pages from '{file.filename}'")

        # Generate embeddings and create nodes
        embed_model = ColPaliEmbedding()
        nodes = embed_model.create_image_nodes(
            images=images,
            image_paths=[str(p) for p in img_paths],
            doc_id=di.document_id,
            source_path=file.filename,
            user_id=user_id,
            ttl_seconds=DOCUMENT_TTL_SECONDS,
        )

        print(f"Generated {len(nodes)} nodes")

        # Store in Qdrant
        qdrant.add_documents(nodes)
        qdrant.finalize_bulk_insert()

        return {
            "message": "Document ingested successfully.",
            "doc_id": di.document_id,
            "filename": file.filename,
            "pages": page_count,
            "expires_in": "24 hours",
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}",
        )

    finally:
        # Track upload end
        quota_manager.end_upload(user_id)
        
        # Cleanup all resources
        if di is not None:
            di.cleanup(delete_saved_images=False)

        if embed_model is not None:
            embed_model.cleanup()

        gc.collect()

@router.get("/quota")
async def get_user_quota(user_id: str = Depends(get_current_user)):
    """
    Get quota information for the authenticated user.
    
    Returns:
        - quota_mb: Total quota in MB
        - used_mb: Used storage in MB
        - remaining_mb: Remaining quota in MB
        - usage_percent: Percentage of quota used
        - concurrent_uploads: Current concurrent uploads
        - max_concurrent: Maximum allowed concurrent uploads
    """
    quota_info = quota_manager.get_user_quota_info(user_id)
    return quota_info
