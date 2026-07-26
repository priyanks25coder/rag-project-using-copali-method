import boto3
from io import BytesIO
from app.config.settings import S3_BUCKET_NAME, AWS_REGION


class S3Storage:
    """Handles S3 image storage and retrieval."""

    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=AWS_REGION)
        self.bucket_name = S3_BUCKET_NAME

    def upload_image(self, image_bytes: bytes, filename: str) -> str:
        """
        Upload image to S3 and return the pre-signed URL.

        Args:
            image_bytes: Image data as bytes
            filename: Filename for the image (e.g., "doc123_page_1.png")

        Returns:
            Pre-signed URL valid for 1 hour
        """
        key = f"images/{filename}"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=image_bytes,
                ContentType='image/png'
            )
            print(f"Uploaded image to S3: s3://{self.bucket_name}/{key}")

            # Generate pre-signed URL (valid for 1 hour)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=3600
            )
            return url

        except Exception as e:
            print(f"Failed to upload image to S3: {e}")
            raise

    def get_presigned_url(self, filename: str, expires_in: int = 3600) -> str:
        """
        Generate a pre-signed URL for an existing image.

        Args:
            filename: Filename in S3
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Pre-signed URL
        """
        key = f"images/{filename}"

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url

        except Exception as e:
            print(f"Failed to generate pre-signed URL: {e}")
            raise

    def delete_image(self, filename: str) -> bool:
        """
        Delete an image from S3.

        Args:
            filename: Filename to delete

        Returns:
            True if successful
        """
        key = f"images/{filename}"

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            print(f"Deleted image from S3: s3://{self.bucket_name}/{key}")
            return True

        except Exception as e:
            print(f"Failed to delete image from S3: {e}")
            return False

    def delete_batch(self, filenames: list) -> int:
        """
        Delete multiple images from S3.

        Args:
            filenames: List of filenames to delete

        Returns:
            Number of successfully deleted files
        """
        if not filenames:
            return 0

        try:
            objects_to_delete = [{'Key': f"images/{fn}"} for fn in filenames]

            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects_to_delete}
            )

            deleted_count = len(response.get('Deleted', []))
            print(f"Deleted {deleted_count} images from S3")
            return deleted_count

        except Exception as e:
            print(f"Failed to delete batch from S3: {e}")
            return 0
