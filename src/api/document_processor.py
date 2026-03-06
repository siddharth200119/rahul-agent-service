from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import List, Optional, Dict, Any
from src.models.api_output import APIOutput as Output
from src.agentic.llms.primary import get_primary_llm, get_vision_llm
from RAW.modals import LLMCapability
from src.utils.file_handler.handler import process_file
from json import loads, JSONDecodeError
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions
import json
from src.services.ocr_service import OCRService
from src.utils.minio_utils import minio_client

primary_llm = get_primary_llm()
vision_llm = get_vision_llm()

router = APIRouter()

@router.post("/process-document")
async def process_document_async(
    document: UploadFile = File(...),
    json_schema: Optional[UploadFile] = File(None),
    json_schema_string: Optional[str] = Form(None),
    priority: str = Form("low")
):
    """
    Submits a document for processing. 
    Stores it in MinIO and adds a task to the OCR queue.
    """
    if json_schema_string and json_schema:
        return Output.failure(message="Please provide either json_schema or json_schema_string")
    
    if json_schema:
        content_bytes = await json_schema.read()
        json_schema_string = content_bytes.decode('utf-8')

    schema = {}
    if json_schema_string:
        try:
            schema = loads(json_schema_string)
            Draft7Validator.check_schema(schema)
        except (JSONDecodeError, jsonschema_exceptions.SchemaError) as e:
            return Output.failure(message=f"Invalid JSON schema: {str(e)}")
    
    # Save file to MinIO
    file_bytes = await document.read()
    file_path = await minio_client.upload_file(file_bytes, document.filename)
    
    # Add to DB queue
    task_id = OCRService.add_to_queue(
        filepath=file_path,
        json_schema=schema,
        priority=priority
    )

    return Output.success(data={"task_id": task_id, "status": "pending"})

@router.get("/task/{task_id}")
async def get_task_status(task_id: int):
    """
    Check the status of a document processing task.
    Returns status and result if available.
    """
    task = OCRService.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    response = {
        "task_id": task["id"],
        "status": task["status"],
        "created_at": task["created_at"]
    }
    
    if task["status"] == "done":
        response["result"] = task["result"]
        
    return Output.success(data=response)

@router.post("/process-document-sync")
async def convert_to_json_sync(
    documents: Optional[List[UploadFile]] = File(None),
    document: Optional[UploadFile] = File(None),
    json_schema: Optional[UploadFile] = File(None),
    json_schema_string: Optional[str] = Form(None)
):
    # Keep the old sync logic for backward compatibility if needed, but renamed
    if not document and not documents:
        return Output.failure(message="At least one document is required")
    
    if json_schema_string and json_schema:
        return Output.failure(message="Please provide either json_schema or json_schema_string")
    
    if json_schema:
        content_bytes = await json_schema.read()
        json_schema_string = content_bytes.decode('utf-8')

    if json_schema_string:
        try:
            schema = loads(json_schema_string)
        except JSONDecodeError:
            return Output.failure(message="Provided schema is not valid JSON")

        try:
            Draft7Validator.check_schema(schema)
        except jsonschema_exceptions.SchemaError as e:
            return Output.failure(message=f"Invalid JSON schema: {e.message}")
    
    all_documents = documents or []
    if document:
        all_documents.append(document)

    texts = {}

    for doc in all_documents:
        file_bytes: bytes = await doc.read()
        texts[doc.filename] = await process_file(file_data=file_bytes, llm=vision_llm, file_path=doc.filename)

    if json_schema_string:
        output = await vision_llm.generate(prompt=f"Convert the following text to JSON based on the provided schema: {texts}", schema=schema)
        output_json = json.loads(output)
        return Output.success(data=output_json)
    return Output.success(data={"texts": texts})
