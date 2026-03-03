import filetype
import hashlib
import json
from typing import Optional, List, Union
from pathlib import Path

from .parsers.excel_parser import excel_parser
from .parsers.image_parser import image_parser
from .parsers.pdf_parser import pdf_parser
from .parsers.text_parser import text_parser
from .parsers.doc_parser import doc_parser
from .parsers.ods_parser import ods_parser
from .parsers.video_parser import video_parser
from .parsers.zip_parser import process_zip_data
from RAW.llms import BaseLLM
from RAW.utils import Logger as ThreadLogger
from typing import Dict, Any

CACHE_FILE = Path("ocr_cache.json")

ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg", "image/bmp", "image/tiff"}
ALLOWED_PDF_MIME = {"application/pdf"}
ALLOWED_EXCEL_MIME = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv"
}
ALLOWED_TEXT_MIME = {"text/plain"}
ALLOWED_DOC_MIME = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
}
ALLOWED_ODS_MIME = {"application/vnd.oasis.opendocument.spreadsheet"}
ALLOWED_ZIP_MIME = {"application/zip"}
ALLOWED_VIDEO_MIME = {"video/mp4", "video/avi", "video/mpeg"}


async def process_file(file_data: Optional[bytes] = None, llm: Optional[BaseLLM] = None, file_path: Optional[Union[Path, str]] = None, logger: Optional[ThreadLogger] = None) -> Union[str, List[Dict[str, Any]]]:
    """Process a file based on its detected type and route to the appropriate parser."""
    if logger:
        logger.debug(message=f"processing file called with file_path and file_data: {file_path}")

    try:
        if file_path is not None and isinstance(file_path, str):
            file_path = Path(file_path)

        if file_path is None and file_data is None:
            raise ValueError("At least file_path or file_data must not be null")

        elif file_data is None and isinstance(file_path, Path):
            file_data = file_path.read_bytes()

        if not isinstance(file_data, bytes):
            raise TypeError("file_data must be of type bytes.")

        file_hash = hashlib.sha256(file_data).hexdigest()

        if logger:
            logger.debug(message=f"Calculated file hash: {file_hash}")

        ocr_cache = {}
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                try:
                    ocr_cache = json.load(f)
                except json.JSONDecodeError:
                    ocr_cache = {}

        if file_hash in ocr_cache:
            if logger:
                logger.info(message=f"Cache hit. Returning stored data for hash: {file_hash}")
            return ocr_cache[file_hash]

        ocr_result = ""

        kind = filetype.guess(file_data)
        mime = kind.mime if kind else None

        if mime is None and file_path:
            extension = None
            if file_path is not None:
                extension = Path(file_path).suffix.lower()
            elif isinstance(file_path, str):
                extension = Path(file_path).suffix.lower()

            if extension:
                mime = {
                    ".txt": "text/plain",
                    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ".odt": "application/vnd.oasis.opendocument.text",
                    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
                    ".zip": "application/zip",
                    ".mp4": "video/mp4",
                    ".avi": "video/avi",
                    ".mpeg": "video/mpeg",
                    ".csv": "text/csv",
                    ".xls": "application/vnd.ms-excel",
                    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    ".pdf": "application/pdf",
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".json": "text/plain",
                }.get(extension, None)

        if logger:
            logger.debug(message=f"Detected mime: {mime}")

        if mime in ALLOWED_IMAGE_MIME:
            if logger:
                logger.debug(message=f"Detected image file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = await image_parser(file_data, llm)

        elif mime in ALLOWED_PDF_MIME:
            if logger:
                logger.debug(message=f"Detected PDF file (mime: {mime}) from {file_path or 'provided bytes'}")
                print("Calling pdf_parser...")
            raw_pages = await pdf_parser(file_data, llm)
            ocr_result = "\n".join([p['text'] for p in raw_pages])

        elif mime in ALLOWED_EXCEL_MIME:
            if logger:
                logger.debug(message=f"Detected Excel/CSV file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = excel_parser(file_data, markdown=True, file_name=str(file_path))

        elif mime in ALLOWED_TEXT_MIME:
            if logger:
                logger.debug(message=f"Detected text file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = text_parser(file_data)

        elif mime in ALLOWED_DOC_MIME:
            if logger:
                logger.debug(message=f"Detected DOC/ODT file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = doc_parser(file_data)

        elif mime in ALLOWED_ODS_MIME:
            if logger:
                logger.debug(message=f"Detected ODS file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = ods_parser(file_data)

        elif mime in ALLOWED_ZIP_MIME:
            if logger:
                logger.debug(message=f"Detected ZIP file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = await process_zip_data(zip_data=file_data, llm=llm, process_file_fn=process_file)

        elif mime in ALLOWED_VIDEO_MIME:
            if logger:
                logger.debug(message=f"Detected video file (mime: {mime}) from {file_path or 'provided bytes'}")
            ocr_result = await video_parser(file_data, llm, fps=1)

        else:
            raise TypeError(
                f"Unsupported file type: {mime or 'Unknown'}. "
                f"Supported types: {', '.join(ALLOWED_IMAGE_MIME | ALLOWED_PDF_MIME | ALLOWED_EXCEL_MIME | ALLOWED_TEXT_MIME | ALLOWED_DOC_MIME | ALLOWED_ODS_MIME | ALLOWED_ZIP_MIME | ALLOWED_VIDEO_MIME)}"
            )

        ocr_cache[file_hash] = ocr_result

        with open(CACHE_FILE, 'w') as f:
            json.dump(ocr_cache, f, indent=4)

        if logger:
            logger.info(message=f"Successfully parsed and stored new data for hash: {file_hash}")

        return ocr_result

    except Exception as e:
        if logger:
            error_message = f'Error processing file (Path: {file_path}, Hash: {file_hash if "file_hash" in locals() else "N/A"}): {e}'
            logger.error(message=error_message, error_obj=e, throwback=True)
        else:
            raise e
        

