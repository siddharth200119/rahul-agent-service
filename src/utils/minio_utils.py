import os
from minio import Minio
from datetime import timedelta
from src.utils import logger

class MinioClient:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9005")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET", "documents")
        self.secure = os.getenv("MINIO_SECURE", "False").lower() == "true"
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None

    async def upload_file(self, file_data: bytes, file_name: str) -> str:
        if not self.client:
            # Fallback to local storage if MinIO is not available
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(file_data)
            return file_path

        import io
        file_stream = io.BytesIO(file_data)
        self.client.put_object(
            self.bucket_name,
            file_name,
            file_stream,
            length=len(file_data)
        )
        return f"{self.bucket_name}/{file_name}"

    def get_file_data(self, file_path: str) -> bytes:
        if not self.client or not ("/" in file_path):
            with open(file_path, "rb") as f:
                return f.read()

        bucket, object_name = file_path.split("/", 1)
        response = self.client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

minio_client = MinioClient()
