import os
from pathlib import Path
from dotenv import load_dotenv

CONFIG_DIR = Path(__file__).resolve().parent
ENV_PATH = CONFIG_DIR / ".env"

load_dotenv(ENV_PATH)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT not in ["development", "staging", "production"]:
    raise ValueError(f"Invalid ENVIRONMENT: {ENVIRONMENT}. Must be 'development', 'staging', or 'production'")

# Qdrant (Critical - requires API key in production)
QDRANT_URL = os.getenv("QDRANT_URL")
if not QDRANT_URL:
    if ENVIRONMENT == "production":
        raise ValueError("QDRANT_URL is required in production")
    QDRANT_URL = "http://localhost:6333"

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if not QDRANT_API_KEY:
    if ENVIRONMENT == "production":
        raise ValueError("QDRANT_API_KEY is required in production")
    QDRANT_API_KEY = ""

QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag-docs")

# ColPali
COLPALI_MODEL_NAME = os.getenv("COLPALI_MODEL_NAME", "vidore/colpali-v1.2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "128"))

# File limits (Safe - non-sensitive configuration)
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "10"))
MAX_PDF_SIZE_BYTES = MAX_PDF_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "20"))

# User quotas (per-user storage limits - Safe - non-sensitive configuration)
USER_QUOTA_MB = int(os.getenv("USER_QUOTA_MB", "100"))  # 100 MB per user
USER_QUOTA_BYTES = USER_QUOTA_MB * 1024 * 1024
USER_CONCURRENT_UPLOADS = int(os.getenv("USER_CONCURRENT_UPLOADS", "3"))  # Max 3 concurrent

# Document TTL (Safe - non-sensitive configuration)
DOCUMENT_TTL_SECONDS = int(os.getenv("DOCUMENT_TTL_SECONDS", "86400"))

# Cleanup (Safe - non-sensitive configuration)
CLEANUP_INTERVAL_HOURS = int(os.getenv("CLEANUP_INTERVAL_HOURS", "6"))

# S3 Configuration (Critical - requires bucket name, AWS credentials via boto3)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME is required - must be set in environment variables")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL")
if not FRONTEND_URL:
    if ENVIRONMENT == "production":
        raise ValueError("FRONTEND_URL is required in production")
    FRONTEND_URL = "http://localhost:5173"

