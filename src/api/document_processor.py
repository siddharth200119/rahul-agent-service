from fastapi import APIRouter, File, Form, UploadFile, Depends, Request
from typing import Optional
from src.models.api_output import APIOutput as Output
from src.agentic.llms.vision import get_vision_llm
from json import loads, JSONDecodeError
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions
import json
import asyncio
from sse_starlette.sse import EventSourceResponse
from src.services.ocr_service import OCRService
from src.middlewares.upload_middleware import upload_to_s3_middleware

vision_llm = get_vision_llm()

router = APIRouter()

@router.post("/process-document")
async def process_document_async(
    file_path: str = Depends(upload_to_s3_middleware),
    json_schema: Optional[UploadFile] = File(None),
    json_schema_string: Optional[str] = Form(None),
    priority: str = Form("low")
):
    """
    Submits a document for processing. 
    The file is uploaded via the upload_middleware.
    Stores metadata in the DB and adds a task to the OCR queue.
    """
    from src.utils import logger
    logger.info(f"Received process-document request: priority='{priority}', json_schema_string='{json_schema_string}'")
    
    if not file_path:
        return Output.failure(message="File is required or failed to upload")

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
    
    # Add to DB queue
    task_id = OCRService.add_to_queue(
        filepath=file_path,
        json_schema=schema,
        priority=priority
    )

    return Output.success(data={"task_id": task_id, "status": "pending"})

@router.get("/task/{task_id}")
async def get_task_status(request: Request, task_id: int):
    """
    Check the status of a document processing task via SSE.
    """
    async def event_generator():
        last_status = None
        while True:
            if await request.is_disconnected():
                break

            task = OCRService.get_task_status(task_id)
            if not task:
                yield {"event": "error", "data": json.dumps({"message": "Task not found"})}
                break

            current_status = task["status"]
            
            # Only send if status changed
            if current_status != last_status:
                data = {
                    "task_id": task["id"],
                    "status": current_status,
                    "created_at": str(task["created_at"])
                }
                if current_status == "done":
                    data["result"] = task["result"]
                    yield {"event": "status", "data": json.dumps(data)}
                    yield {"event": "done", "data": "Processing complete"}
                    break
                elif current_status == "failed":
                    data["error"] = task.get("error", "Unknown error")
                    yield {"event": "status", "data": json.dumps(data)}
                    break
                
                yield {"event": "status", "data": json.dumps(data)}
                last_status = current_status

            await asyncio.sleep(2)  # Poll every 2 seconds

    return EventSourceResponse(event_generator())
