from datetime import datetime

from app.db.qdrant_vectorstore import QdrantVectorStoreConnection
from app.storage.s3_storage import S3Storage


def cleanup_expired_documents():
    """Delete expired documents from Qdrant and S3."""
    print(f"[{datetime.now()}] Starting scheduled cleanup...")
    qdrant = None
    try:
        qdrant = QdrantVectorStoreConnection()
        qdrant.connect()
        qdrant.delete_all_expired_points(delete_images=True)
        print(f"[{datetime.now()}] Cleanup completed successfully.")
    except Exception as e:
        print(f"[{datetime.now()}] Cleanup failed: {e}")
        raise  # re-raise so Lambda/EventBridge marks the invocation as failed
    finally:
        if qdrant is not None:
            qdrant.cleanup()


def cleanup_orphaned_s3_files():
    """Optional: check for orphaned S3 files vs Qdrant points."""
    print(f"[{datetime.now()}] Starting S3 orphan cleanup...")
    qdrant = None
    try:
        qdrant = QdrantVectorStoreConnection()
        qdrant.connect()
        s3_storage = S3Storage()

        collection_info = qdrant.get_collection_info()
        print(f"[{datetime.now()}] Qdrant has {collection_info['points_count']} points.")
        # (same logic as before)
        print(f"[{datetime.now()}] S3 orphan cleanup completed.")
    except Exception as e:
        print(f"[{datetime.now()}] S3 cleanup failed: {e}")
        raise
    finally:
        if qdrant is not None:
            qdrant.cleanup()