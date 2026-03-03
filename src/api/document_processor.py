from fastapi import APIRouter, File, Form, UploadFile
from typing import List, Optional
from src.models.api_output import APIOutput as Output
from src.agentic.llms.primary import get_primary_llm, get_vision_llm
from RAW.modals import LLMCapability
from src.utils.file_handler.handler import process_file
from json import loads, JSONDecodeError
from jsonschema import Draft7Validator, exceptions as jsonschema_exceptions
import json

primary_llm = get_primary_llm()
vision_llm = get_vision_llm()

router = APIRouter()

@router.post("/process-document")
async def convert_to_json(
    documents: Optional[List[UploadFile]] = File(None),
    document: Optional[UploadFile] = File(None),
    json_schema: Optional[UploadFile] = File(None),
    json_schema_string: Optional[str] = Form(None)
):
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