import gc
import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image
import fitz

from app.storage.s3_storage import S3Storage


class DocumentIngestion:
    """Handles document ingestion and page extraction with S3 storage."""

    def __init__(self, file_bytes: bytes = None, filename: str = "", document_path: str = ""):
        self.file_bytes = file_bytes
        self.filename = filename
        self.document_path = document_path
        
        # S3 storage is mandatory
        self.s3_storage = S3Storage()

        self.document_pages_img = []
        self.document_pages_path = []  # S3 pre-signed URLs
        self.document_filenames = []   # For cleanup
        self.document_id = None

    def set_document_id(self) -> str:
        """Generate and set a unique document ID."""
        self.document_id = str(uuid.uuid4())
        return self.document_id

    def get_pdf_pages(self) -> list:
        """Extract pages from PDF bytes and upload to S3."""
        if len(self.document_pages_path) > 0:
            return self.document_pages_path

        doc = None

        try:
            if self.file_bytes:
                doc = fitz.open(stream=self.file_bytes, filetype="pdf")
            else:
                doc = fitz.open(self.document_path)

            total_pages = len(doc)
            print(f"Total pages in PDF: {total_pages}")

            for page_num in range(total_pages):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=150)

                filename = f"{self.document_id}_page_{page_num + 1}.png"
                self.document_filenames.append(filename)

                # Upload to S3
                image_bytes = pix.tobytes("png")
                url = self.s3_storage.upload_image(image_bytes, filename)
                self.document_pages_path.append(url)
                print(f"Uploaded page {page_num + 1} to S3")

                # Convert to PIL Image for processing
                pil_image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples,
                )
                self.document_pages_img.append(pil_image)

                del pix
                del page

            print(f"Extracted and uploaded {len(self.document_pages_path)} pages to S3.")

        finally:
            if doc is not None:
                doc.close()
                del doc
            gc.collect()

        return self.document_pages_path

    def cleanup(self, delete_saved_images: bool = False):
        """Free memory and optionally delete images from S3."""
        # Close PIL images
        for img in self.document_pages_img:
            if img is not None:
                try:
                    img.close()
                except Exception:
                    pass

        # Delete saved images from S3 if requested
        if delete_saved_images:
            if self.document_filenames:
                self.s3_storage.delete_batch(self.document_filenames)
                print(f"Deleted {len(self.document_filenames)} images from S3")

        self.document_pages_img.clear()
        self.document_pages_path.clear()
        self.document_filenames.clear()
        self.file_bytes = None

        gc.collect()
        print("Document memory cleaned up.")