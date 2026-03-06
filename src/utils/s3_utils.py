import os
from minio import Minio
from datetime import timedelta
from src.utils import logger
import io

class S3Util:
    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT", os.getenv("MINIO_ENDPOINT", "localhost:9005"))
        self.access_key = os.getenv("S3_ACCESS_KEY", os.getenv("MINIO_ACCESS_KEY", "minioadmin"))
        self.secret_key = os.getenv("S3_SECRET_KEY", os.getenv("MINIO_SECRET_KEY", "minioadmin"))
        self.bucket_name = os.getenv("S3_BUCKET", os.getenv("MINIO_BUCKET", "documents"))
        self.secure = os.getenv("S3_SECURE", os.getenv("MINIO_SECURE", "False")).lower() == "true"
        
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
            logger.error(f"Failed to initialize S3 client: {e}")
            self.client = None

    async def upload_file(self, file_data: bytes, file_name: str) -> str:
        if not self.client:
            # Fallback to local storage if S3 is not available
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(file_data)
            return file_path

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
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    return f.read()
            return None

        parts = file_path.split("/", 1)
        if len(parts) < 2:
            return None
        bucket, object_name = parts[0], parts[1]
        
        try:
            response = self.client.get_object(bucket, object_name)
            return response.read()
        except Exception as e:
            logger.error(f"Failed to get file data from S3: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()

s3_client = S3Util()
