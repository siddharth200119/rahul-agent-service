import asyncio
import json
import os
from dotenv import load_dotenv
from src.utils.redis import get_redis
from src.services.so_validation import SOValidationService
from src.utils import logger

load_dotenv()

SO_QUEUE = "so_validation_queue"
SO_RESULT_PREFIX = "so_validation:result:{}"
SO_INPUT_PREFIX = "so_validation:input:{}"

async def process_so_job(request_id: str):
    logger.info(f"Processing SO Validation request: {request_id}")
    r = await get_redis()
    
    try:
        # 1. Get input data from Redis
        input_key = SO_INPUT_PREFIX.format(request_id)
        input_data_json = await r.get(input_key)
        
        if not input_data_json:
            logger.error(f"Input data for {request_id} not found")
            return
            
        input_data = json.loads(input_data_json)
        
        # 2. Execute Validation Service
        results = await SOValidationService.validate_so(
            input_data['product_ids'],
            input_data['quantities'],
            input_data['weights']
        )
        
        # 3. Store result back in Redis (TTL: 1 hour)
        result_key = SO_RESULT_PREFIX.format(request_id)
        await r.setex(result_key, 3600, json.dumps(results))
        
        # 4. Cleanup input data
        await r.delete(input_key)
        
        logger.info(f"Successfully processed SO Validation: {request_id}")

    except Exception as e:
        logger.error(f"Worker error processing request {request_id}: {e}")
        # Store error result so user knows why it failed
        error_res = [{"status": "error", "message": str(e)}]
        await r.setex(SO_RESULT_PREFIX.format(request_id), 3600, json.dumps(error_res))

async def main():
    logger.info("Starting SO Validation Worker...")
    r = await get_redis()
    
    while True:
        try:
            # Blocking pop from queue
            job = await r.blpop(SO_QUEUE, timeout=5)
            if job:
                request_id = job[1]
                asyncio.create_task(process_so_job(request_id))
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"SO Worker main loop error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
