from fastapi import APIRouter, BackgroundTasks, Request, Header
from src.models import APIOutput
from src.services.performance_service import PerformanceService
from src.utils.redis import wait_for_stream_item, get_message_state, get_stream_history
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import uuid
import json
import asyncio
from typing import Optional

router = APIRouter()

@router.post("/performance", response_model=APIOutput)
async def create_performance_report(
    background_tasks: BackgroundTasks, 
    grn_number: str = Header(..., alias="grn_number")
):
    try:
        report_id = str(uuid.uuid4())
        
        # Start report generation in background
        background_tasks.add_task(PerformanceService.generate_performance_report, report_id, grn_number)
        
        return APIOutput.success(
            data={"report_id": report_id},
            message="data received and report will be generated"
        )
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.get("/performance/{report_id}")
async def get_performance_report(report_id: str, request: Request):
    """
    Stream the performance report results using SSE
    """
    async def event_generator():
        last_index = 0
        while True:
            # If client disconnects, stop streaming
            if await request.is_disconnected():
                break

            # Wait for new chunks in Redis
            chunks = await wait_for_stream_item(report_id, last_index, timeout=5)
            
            if chunks:
                for chunk in chunks:
                    yield {
                        "event": "message",
                        "data": json.dumps({"chunk": chunk})
                    }
                last_index += len(chunks)

            # Check if processing is finished
            state = await get_message_state(report_id)
            if state.get("status") in ["done", "error"]:
                # One last check for any remaining chunks
                final_chunks = await wait_for_stream_item(report_id, last_index, timeout=1)
                for chunk in final_chunks:
                     yield {
                        "event": "message",
                        "data": json.dumps({"chunk": chunk})
                    }
                
                # Send completion event
                yield {
                    "event": "end",
                    "data": json.dumps({"status": state.get("status"), "error": state.get("error", None)})
                }
                break
            
            await asyncio.sleep(0.1)

    return EventSourceResponse(event_generator())

@router.get("/performance/result/{report_id}", response_model=APIOutput)
async def get_performance_report_result(report_id: str):
    """
    Get the full performance report results (non-streaming)
    """
    try:
        state = await get_message_state(report_id)
        if not state:
            return APIOutput.failure(message="Report not found", status_code=404)
        
        chunks = await get_stream_history(report_id)
        full_report = "".join(chunks)
        
        return APIOutput.success(
            data={
                "status": state.get("status"),
                "report": full_report,
                "error": state.get("error")
            },
            message="Report retrieved successfully"
        )
    except Exception as e:
        return APIOutput.failure(message=str(e))
