import hmac
import hashlib
import time
import uuid
import os
from typing import Optional


class UserIDManager:
    """Generates and verifies HMAC-signed user IDs"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv('USER_ID_SECRET', '120ab41d24cd225008bcd5e6ef58e72dcd662dc226e16')
    
    def generate_user_id(self) -> str:
        """
        Generate a signed user ID token.
        Format: {uuid}.{timestamp}.{signature}
        """
        user_uuid = str(uuid.uuid4())
        timestamp = str(int(time.time() * 1000))  # milliseconds
        
        # Create data to sign
        data = f"{user_uuid}.{timestamp}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{data}.{signature}"
    
    def verify_user_id(self, token: str, max_age_seconds: int = 30 * 24 * 60 * 60) -> Optional[str]:
        """
        Verify a signed user ID token.
        Returns the user UUID if valid, None if tampered or expired.
        
        Args:
            token: The signed user ID token
            max_age_seconds: Maximum age of token in seconds (default: 30 days)
        
        Returns:
            The user UUID if valid, None otherwise
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            user_uuid, timestamp_str, signature = parts
            
            # Verify signature
            data = f"{user_uuid}.{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None  # Tampered
            
            # Check expiration
            timestamp = int(timestamp_str)
            current_time = int(time.time() * 1000)
            age_ms = current_time - timestamp
            age_seconds = age_ms / 1000
            
            if age_seconds > max_age_seconds:
                return None  # Expired
            
            return user_uuid
        
        except (ValueError, IndexError):
            return None


# Singleton instance
_user_id_manager = None

def get_user_id_manager() -> UserIDManager:
    """Get or create the UserIDManager singleton"""
    global _user_id_manager
    if _user_id_manager is None:
        _user_id_manager = UserIDManager()
    return _user_id_manager
