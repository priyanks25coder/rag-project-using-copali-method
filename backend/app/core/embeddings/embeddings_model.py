import gc
import time
import torch
import numpy as np
from pathlib import Path
from typing import List, Optional
from PIL import Image
from colpali_engine.models import ColPali, ColPaliProcessor
from dataclasses import dataclass
from urllib.parse import urlparse

from config.settings import COLPALI_MODEL_NAME, EMBEDDING_DIM

@dataclass
class PageNode:
    image_path: str
    text: str
    embedding: List
    metadata: dict


class ColPaliEmbedding:
    """ColPali embedding model for document images and text queries."""

    def __init__(
        self,
        model_name: str = COLPALI_MODEL_NAME,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None
        self._processor = None
        self._load_model()

    def _load_model(self):
        """Download and load ColPali model and processor."""
        print(f"Loading {self.model_name} on {self.device}...")

        if self.device == "cpu":
            self._model = ColPali.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True,
                device_map="cpu",
            ).eval()
        else:
            self._model = ColPali.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
            ).to(self.device).eval()

        self._processor = ColPaliProcessor.from_pretrained(self.model_name)
        print("Model loaded successfully.")

    def cleanup(self):
        """Unload model and free memory."""
        if self._model is not None:
            del self._model
            self._model = None

        if self._processor is not None:
            del self._processor
            self._processor = None

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("Model unloaded.")

    @torch.no_grad()
    def embed_images(self, images: List[Image.Image]) -> List[np.ndarray]:
        """Generate patch-level multi-vector embeddings for page images."""
        embeddings = []
        batch_size = 1

        for i in range(0, len(images), batch_size):
            batch = self._processor.process_images(
                images[i : i + batch_size]
            ).to(self.device)

            if self.device == "cuda":
                with torch.amp.autocast("cuda"):
                    batch_embeddings = self._model(**batch)
            else:
                batch_embeddings = self._model(**batch)

            for emb in batch_embeddings:
                embeddings.append(emb.cpu().float().numpy())

            del batch
            del batch_embeddings
            gc.collect()

        return embeddings

    @torch.no_grad()
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Generate token-level multi-vector embeddings for text queries."""
        embeddings = []

        for text in texts:
            batch = self._processor.process_queries([text]).to(self.device)

            if self.device == "cuda":
                with torch.amp.autocast("cuda"):
                    text_embeddings = self._model(**batch)
            else:
                text_embeddings = self._model(**batch)

            embeddings.append(text_embeddings[0].cpu().float().numpy())

            del batch
            del text_embeddings
            gc.collect()

        return embeddings

    def create_image_nodes(
        self,
        images: List[Image.Image],
        image_paths: List[str],
        doc_id: str,
        source_path: str,
        user_id: str = "",
        ttl_seconds: int = 86400,
    ) -> List[PageNode]:
        """Generate embeddings and build PageNodes with TTL metadata."""

        if not images:
            raise ValueError("No images provided.")

        if len(images) != len(image_paths):
            raise ValueError("Number of images must match number of image_paths.")

        total_pages = len(images)
        created_at = int(time.time())
        expires_at = created_at + ttl_seconds

        print(f"Processing {total_pages} pages from '{doc_id}'...")

        embeddings = self.embed_images(images)
        print(f"Embeddings shape: {embeddings[0].shape}")

        nodes = [
            PageNode(
                image_path=image_path,  # S3 pre-signed URL
                text=f"Page {page_num} of {doc_id}",
                embedding=embedding.tolist(),
                metadata={
                    "user_id":     user_id,
                    "doc_id":      doc_id,
                    "source":      source_path,
                    "page":        page_num,
                    "total_pages": total_pages,
                    "image_url":   image_path,  # S3 pre-signed URL
                    "image_name":  Path(urlparse(image_path).path).name,  # Filename from URL
                    "file_type":   Path(source_path).suffix.lstrip(".").lower(),
                    "created_at":  created_at,
                    "expires_at":  expires_at,
                },
            )
            for page_num, (image_path, embedding) in enumerate(
                zip(image_paths, embeddings), start=1
            )
        ]

        print(f"Created {len(nodes)} PageNodes for '{doc_id}'")
        return nodes