from fastapi import Request, UploadFile, File
from src.utils.s3_utils import s3_client
from typing import Dict, Any, Optional

async def upload_to_s3_middleware(document: Optional[UploadFile] = File(None)):
    """
    FastAPI dependency that uploads a file to S3 and returns the file path.
    Can be used in route handlers to replace UploadFile with a string path.
    """
    if not document:
        return None
        
    try:
        content = await document.read()
        if not content:
            return None
            
        file_path = await s3_client.upload_file(content, document.filename)
        return file_path
    except Exception as e:
        from src.utils import logger
        logger.error(f"Error in upload_middleware: {str(e)}")
        return None

async def handle_multiple_uploads(documents: Optional[list[UploadFile]] = File(None)):
    """
    FastAPI dependency that uploads multiple files to S3 and returns a list of paths.
    """
    if not documents:
        return []
        
    paths = []
    for doc in documents:
        if doc.filename:
            content = await doc.read()
            path = await s3_client.upload_file(content, doc.filename)
            paths.append(path)
    return paths
