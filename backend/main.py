from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config.settings import FRONTEND_URL
from app.api.routes import ingest, search, sessions, fetch_image, auth
from app.db.qdrant_vectorstore import QdrantVectorStoreConnection
from app.core.middleware import verify_user_id_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    qdrant = QdrantVectorStoreConnection()
    qdrant.connect()
    qdrant.setup_collection_schema()
    app.state.qdrant = qdrant
    print("Application started.")
    yield
    if hasattr(app.state, 'qdrant'):
        app.state.qdrant.cleanup()
    print("Application stopped.")


app = FastAPI(
    title="RAG API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add user ID verification middleware
app.middleware("http")(verify_user_id_middleware)

# Register routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(fetch_image.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}