import time

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PayloadSchemaType,
    PointIdsList,
    Range,
    VectorParams,
    MultiVectorConfig,
    MultiVectorComparator,
    Filter,
    FieldCondition,
    MatchValue,
    PointStruct,
    ScalarQuantization,
    ScalarQuantizationConfig,
    ScalarType,
    OptimizersConfigDiff
)
import os
import gc
import uuid
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = CONFIG_DIR / ".env"
load_dotenv(ENV_PATH)


class QdrantVectorStoreConnection:
    """Manages Qdrant vector database connection for ColPali multi-vector storage."""

    def __init__(
        self,
        url: str = os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key: str = os.getenv("QDRANT_API_KEY", ""),
        collection_name: str = os.getenv("QDRANT_COLLECTION_NAME", "rag-docs"),
        embedding_dim: int = 128,
    ):
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.client = None

    def __enter__(self):
        """Support for 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting 'with' block."""
        self.cleanup()
        return False

    def cleanup(self):
        """Close Qdrant connection and free memory."""
        if self.client is not None:
            try:
                self.client.close()
            except Exception as e:
                print(f"Error closing Qdrant client: {e}")
            finally:
                del self.client
                self.client = None
        gc.collect()
        print("Qdrant connection closed and memory cleaned up.")

    def connect(self):
        """Establish connection to Qdrant."""
        try:
            kwargs = {"url": self.url}
            if self.api_key:
                kwargs["api_key"] = self.api_key

            self.client = QdrantClient(**kwargs)
            self.client.get_collections()
            print(f"Connected to Qdrant")

        except Exception as e:
            print(f"Failed to connect to Qdrant: {e}")
            raise

    def setup_collection_schema(self):
        """Create collection with Multi-Vector Config for ColPali if not exists."""
        if self.client is None:
            self.connect()

        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                print(f"Creating new collection '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE,
                        multivector_config=MultiVectorConfig(
                            comparator=MultiVectorComparator.MAX_SIM,
                        ),
                        quantization_config=ScalarQuantization(
                            scalar=ScalarQuantizationConfig(
                                type=ScalarType.INT8,
                                quantile=0.99,
                                always_ram=True,   # Keep quantized vectors in RAM for speed
                            )
                        ),
                    ),
                    replication_factor=1,
                    # Optimizer config for bulk insert
                    optimizers_config=OptimizersConfigDiff(
                        indexing_threshold=0,      # Disable auto-indexing during bulk load
                        memmap_threshold=20000,    # Use memmap for larger segments
                    ),
                )
                print(f"Created collection '{self.collection_name}' successfully.")

                index_fields = [
                    ("user_id",      PayloadSchemaType.KEYWORD),
                    ("doc_id",       PayloadSchemaType.KEYWORD),
                    ("page",         PayloadSchemaType.INTEGER),
                    ("expires_at",   PayloadSchemaType.INTEGER),
                    ("file_type",    PayloadSchemaType.KEYWORD),
                    ("created_at",   PayloadSchemaType.INTEGER),
                ]

                for field_name, field_type in index_fields:
                    try:
                        self.client.create_payload_index(
                            collection_name=self.collection_name,
                            field_name=field_name,
                            field_schema=field_type,
                            wait=True,  # Wait for index build
                        )
                        print(f"  ✓ Created payload index: {field_name} ({field_type})")
                    except Exception as e:
                        # Index might already exist if re-running script
                        print(f"  ⚠ Index '{field_name}' skipped: {e}")

                print(f"Collection '{self.collection_name}' is ready with schema and indexes.")
            else:
                print(f"Collection '{self.collection_name}' already exists.")
                self._ensure_payload_indexes_exist()

        except Exception as e:
            print(f"Failed to create collection schema: {e}")
            raise
    
    def _ensure_payload_indexes_exist(self):
        """Idempotently create indexes if collection already existed."""
        index_fields = [
            ("user_id",    PayloadSchemaType.KEYWORD),
            ("doc_id",     PayloadSchemaType.KEYWORD),
            ("page",       PayloadSchemaType.INTEGER),
            ("expires_at", PayloadSchemaType.INTEGER),
            ("file_type",  PayloadSchemaType.KEYWORD),
            ("created_at", PayloadSchemaType.INTEGER),
        ]
        for field_name, field_type in index_fields:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=field_type,
                    wait=False,  # Don't block startup
                )
            except Exception:
                pass  # Already exists or not needed

    def finalize_bulk_insert(self):
        """
        Call this ONCE after all `add_documents()` calls are done.
        Re-enables automatic indexing so search works correctly.
        """
        if self.client is None:
            self.connect()

        try:
            print("Finalizing bulk insert: enabling indexing...")
            self.client.update_collection(
                collection_name=self.collection_name,
                optimizer_config=OptimizersConfigDiff(indexing_threshold=20000),
            )
            print("Indexing enabled. Qdrant will now build indexes in background.")
        except Exception as e:
            print(f"Failed to update collection optimizer config: {e}")
            raise


    def add_documents(self, nodes: List) -> None:
        """
        Insert PageNodes into Qdrant.

        Args:
            nodes: List of PageNodes with pre-computed ColPali embeddings
        """
        if self.client is None:
            self.connect()

        try:
            points = []
            for node in nodes:
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=node.embedding,
                    payload=node.metadata,
                )
                points.append(point)

            print(f"Adding {len(points)} documents to collection '{self.collection_name}'...")

            batch_size = 1
            self.client.upload_points(
                collection_name=self.collection_name,
                points=points,
                wait=False,
                batch_size=batch_size,
                parallel=2,
                max_retries=3
            )

            print(f"Added {len(nodes)} documents to '{self.collection_name}'.")

        except Exception as e:
            print(f"Failed to add documents: {e}")
            raise

        finally:
            del points
            gc.collect()

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search Qdrant using ColPali multi-vector MaxSim scoring.

        Args:
            query_embedding: Query embedding array of shape (num_tokens, 128)
            top_k:           Number of results to return
            filters:         Optional metadata filters e.g. {"doc_id": "report"}

        Returns:
            List of dicts with score and metadata
        """
        if self.client is None:
            self.connect()

        try:
            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filters.items()
                ]
                query_filter = Filter(must=conditions)

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=top_k,
                query_filter=query_filter,
                with_payload=True,
            )

            search_results = [
                {
                    "id" :   point.id,
                    "score":    point.score,
                    "metadata": point.payload,
                }
                for point in results.points
            ]

            print(f"Search returned {len(search_results)} results for filters={filters}")

            return search_results

        except Exception as e:
            print(f"Search failed: {e}")
            raise

        finally:
            del results
            gc.collect()

    def delete_collection(self):
        """Delete the collection."""
        if self.client is None:
            self.connect()

        try:
            self.client.delete_collection(collection_name=self.collection_name)
            print(f"Collection '{self.collection_name}' deleted.")
        except Exception as e:
            print(f"Failed to delete collection: {e}")
            raise

    def get_collection_info(self) -> Dict:
        """Get collection statistics."""
        if self.client is None:
            self.connect()

        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name":          self.collection_name,
                "points_count":  info.points_count,
                "vectors_count": info.vectors_count,
                "status":        info.status,
            }
        except Exception as e:
            print(f"Failed to get collection info: {e}")
            raise

        finally:
            del info
            gc.collect()
    
    def delete_points_by_user_id(self, user_id: str):
        """Delete points from the collection based on user_id."""
        if self.client is None:
            self.connect()

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    )
                ]),
                wait=True,
            )
            print(f"Deleted points for user_id '{user_id}' from collection '{self.collection_name}'.")

        except Exception as e:
            print(f"Failed to delete points for user_id '{user_id}': {e}")
            raise

    def delete_all_points(self, batch_size: int = 100):
        """Delete all points from the collection while keeping the collection schema."""
        if self.client is None:
            self.connect()

        try:
            total_deleted = 0
            offset = None

            while True:
                records, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False,
                )

                if not records:
                    break

                point_ids = [record.id for record in records]

                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=PointIdsList(points=point_ids),
                    wait=True,
                )

                total_deleted += len(point_ids)
                print(f"Deleted {total_deleted} points so far...")

                offset = next_offset

                del records
                del point_ids
                gc.collect()

                if offset is None:
                    break

            print(f"Deleted all points from collection '{self.collection_name}'.")

        except Exception as e:
            print(f"Failed to delete all points: {e}")
            raise

        finally:
            gc.collect()

    def delete_all_expired_points(self, delete_images: bool = False, batch_size: int = 100):
        """
        Delete all expired points from the collection while keeping the collection schema.
        
        Args:
            delete_images: If True, delete associated images from S3
            batch_size: Number of points to process per batch
        """
        if self.client is None:
            self.connect()

        try:
            from app.storage.s3_storage import S3Storage
            s3_storage = S3Storage() if delete_images else None
            
            total_deleted = 0
            offset = None

            while True:
                records, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False,
                    scroll_filter=Filter(must=[
                        FieldCondition(
                            key="expires_at",
                            range = Range(lte=int(time.time())),
                        )
                    ])
                )

                if not records:
                    break
                    
                point_ids = []
                image_names = []

                for record in records:
                    point_ids.append(record.id)

                    if record.payload and "image_name" in record.payload:
                        image_names.append(record.payload["image_name"])

                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=PointIdsList(points=point_ids),
                    wait=True,
                )

                # Delete images from S3 if requested
                if delete_images and image_names and s3_storage:
                    try:
                        deleted_count = s3_storage.delete_batch(image_names)
                        print(f"Deleted {deleted_count} images from S3")
                    except Exception as e:
                        print(f"Failed to delete images from S3: {e}")

                total_deleted += len(point_ids)
                print(f"Deleted {total_deleted} expired points so far.")

                offset = next_offset

                del records
                del point_ids
                del image_names
                gc.collect()

                if offset is None:
                    break

            print(f"Deleted {total_deleted} expired points from '{self.collection_name}'.")

        except Exception as e:
            print(f"Failed to delete expired points: {e}")
            raise

        finally:
            gc.collect()