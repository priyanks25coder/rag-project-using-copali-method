import time
from typing import Dict, Tuple
from app.config.settings import USER_QUOTA_BYTES, USER_CONCURRENT_UPLOADS
from app.db.qdrant_vectorstore import QdrantVectorStoreConnection


class QuotaManager:
    """Manages per-user storage quotas and concurrent upload limits."""

    def __init__(self):
        self.qdrant = QdrantVectorStoreConnection()
        # In-memory tracking for concurrent uploads (reset on app restart)
        self.active_uploads: Dict[str, int] = {}

    def get_user_storage_usage(self, user_id: str) -> int:
        """
        Calculate total storage used by a user based on their Qdrant documents.
        
        Args:
            user_id: User session ID
        
        Returns:
            Total bytes used by this user
        """
        try:
            self.qdrant.connect()
            
            # Get all points for this user
            results = self.qdrant.search(
                query_embedding=[[0] * 128],  # Dummy query to get all
                top_k=10000,
                filters={"user_id": user_id}
            )
            
            # Estimate size: average image ~300KB per page
            # This is approximate - real size would require querying S3
            estimated_bytes_per_point = 300 * 1024  # 300 KB per image
            total_usage = len(results) * estimated_bytes_per_point
            
            return total_usage
            
        except Exception as e:
            print(f"Error calculating user storage: {e}")
            return 0
        finally:
            self.qdrant.cleanup()

    def get_user_quota_remaining(self, user_id: str) -> int:
        """
        Get remaining quota for a user.
        
        Args:
            user_id: User session ID
        
        Returns:
            Remaining bytes available for upload
        """
        usage = self.get_user_storage_usage(user_id)
        remaining = max(0, USER_QUOTA_BYTES - usage)
        return remaining

    def can_upload(self, user_id: str, file_size_bytes: int) -> Tuple[bool, str]:
        """
        Check if user can upload a file.
        
        Args:
            user_id: User session ID
            file_size_bytes: Size of file to upload
        
        Returns:
            Tuple of (can_upload: bool, reason: str)
        """
        # Check concurrent uploads
        concurrent_count = self.active_uploads.get(user_id, 0)
        if concurrent_count >= USER_CONCURRENT_UPLOADS:
            return False, f"Too many concurrent uploads. Max {USER_CONCURRENT_UPLOADS} allowed."
        
        # Check storage quota
        remaining = self.get_user_quota_remaining(user_id)
        if file_size_bytes > remaining:
            used_mb = self.get_user_storage_usage(user_id) / (1024 * 1024)
            quota_mb = USER_QUOTA_BYTES / (1024 * 1024)
            return False, (
                f"Storage quota exceeded. "
                f"Used: {used_mb:.1f}MB / {quota_mb:.1f}MB. "
                f"Please delete some documents first."
            )
        
        return True, "OK"

    def start_upload(self, user_id: str):
        """Track that user started an upload."""
        self.active_uploads[user_id] = self.active_uploads.get(user_id, 0) + 1

    def end_upload(self, user_id: str):
        """Track that user finished an upload."""
        count = self.active_uploads.get(user_id, 0)
        if count > 0:
            self.active_uploads[user_id] = count - 1
        else:
            self.active_uploads[user_id] = 0

    def get_user_quota_info(self, user_id: str) -> Dict:
        """
        Get detailed quota information for a user.
        
        Args:
            user_id: User session ID
        
        Returns:
            Dictionary with quota details
        """
        usage = self.get_user_storage_usage(user_id)
        remaining = self.get_user_quota_remaining(user_id)
        concurrent = self.active_uploads.get(user_id, 0)
        
        return {
            "user_id": user_id,
            "quota_mb": USER_QUOTA_BYTES / (1024 * 1024),
            "used_mb": usage / (1024 * 1024),
            "remaining_mb": remaining / (1024 * 1024),
            "usage_percent": (usage / USER_QUOTA_BYTES * 100) if USER_QUOTA_BYTES > 0 else 0,
            "concurrent_uploads": concurrent,
            "max_concurrent": USER_CONCURRENT_UPLOADS,
        }
