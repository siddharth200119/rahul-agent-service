import asyncio
import json
import logging
from src.utils import logger
from src.services.ocr_service import OCRService
from src.utils.s3_utils import s3_client
from src.utils.file_handler.handler import process_file
from src.agentic.llms.vision import get_vision_llm

vision_llm = get_vision_llm()

async def process_ocr_task(task):
    task_id = task['id']
    file_path = task['filepath']
    schema = task['json_schema']
    
    logger.info(f"Worker processing OCR task {task_id}: {file_path}")
    
    try:
        # 1. Fetch file from S3
        file_bytes = s3_client.get_file_data(file_path)
        
        # 2. Extract text from file
        # We use process_file which routes to appropriate parser based on extension/mime
        # Note: file_path here might be "bucket/name", so we should get the filename part for process_file
        filename = file_path.split("/")[-1]
        extracted_text = await process_file(file_data=file_bytes, llm=vision_llm, file_path=filename)
        
        # 3. Use LLM to convert to JSON if schema is provided
        if schema and isinstance(schema, dict) and len(schema) > 0:
            prompt = f"Convert the following text to JSON based on the provided schema: {extracted_text}"
            output = await vision_llm.generate(prompt=prompt, schema=schema)
            try:
                result = json.loads(output)
            except json.JSONDecodeError:
                # LLM might return a string that is not valid JSON despite the schema request
                # In a real scenario, we might want to retry or fix it
                result = {"raw_output": output, "error": "LLM output was not valid JSON"}
        else:
            result = {"text": extracted_text}
        
        # 4. Update task as done
        OCRService.update_task_result(task_id, result)
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing OCR task {task_id}: {e}")
        OCRService.update_task_status(task_id, 'failed')

async def main():
    logger.info("Starting OCR Worker...")
    while True:
        try:
            # Poll for next task
            task = OCRService.get_next_task()
            
            if task:
                # Process task asynchronously or synchronously? 
                # Synchronous per-worker is usually safer for LLM load balancing, 
                # but we can do create_task if we want parallel processing in one worker.
                # For now, let's process one by one to respect the "one by one" request.
                await process_ocr_task(task)
            else:
                # Wait a bit before polling again
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"OCR Worker loop error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
