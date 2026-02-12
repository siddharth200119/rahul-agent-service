from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import uuid
import json
from src.models import APIOutput
from src.utils.redis import get_redis

router = APIRouter()

SO_QUEUE = "so_validation_queue"
SO_RESULT_PREFIX = "so_validation:result:{}"
SO_INPUT_PREFIX = "so_validation:input:{}"

class SOValidatorRequest(BaseModel):
    product_ids: List[int]
    quantities: List[float]
    weights: List[float]

@router.post("/so/validate")
async def validate_so(data: SOValidatorRequest):
    try:
        # 1. Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # 2. Store input data for the worker to pick up
        r = await get_redis()
        input_key = SO_INPUT_PREFIX.format(request_id)
        await r.setex(input_key, 300, data.json()) # 5 min TTL for input
        
        # 3. Push job to the queue
        await r.rpush(SO_QUEUE, request_id)
        
        return APIOutput.success(
            data={"request_id": request_id}, 
            message="Input received, validation started in background."
        )
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.get("/so/results/{request_id}")
async def get_so_results(request_id: str):
    try:
        r = await get_redis()
        result_key = SO_RESULT_PREFIX.format(request_id)
        data = await r.get(result_key)
        
        if not data:
            # Check if it's still pending
            input_key = SO_INPUT_PREFIX.format(request_id)
            is_pending = await r.exists(input_key)
            if is_pending:
                return APIOutput.success(message="Validation is still in progress. Please try again in 2-3 seconds.", status_code=202)
            
            return APIOutput.failure(message="Results not found or expired.", status_code=404)
        
        return APIOutput.success(data=json.loads(data))
    except Exception as e:
        return APIOutput.failure(message=str(e))
