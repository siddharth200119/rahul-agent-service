import asyncio
import logging
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from src.utils.redis import get_stream_history, wait_for_stream_item, get_message_state

router = APIRouter(prefix="/sse")
logger = logging.getLogger(__name__)

@router.get("/message-reply/{message_id}")
async def stream_message_reply(request: Request, message_id: int):
    """
    Stream the reply for a given message ID using Server-Sent Events (SSE).
    """
    async def event_generator():
        # 1. Send existing history
        history = await get_stream_history(message_id)
        current_index = 0
        
        for chunk in history:
            current_index += 1
            yield {"data": chunk}

        # 2. Poll for new chunks
        while True:
            if await request.is_disconnected():
                logger.info(f"Client disconnected from stream {message_id}")
                break

            # Poll for new items
            new_chunks = await wait_for_stream_item(message_id, current_index, timeout=2) # Short timeout for responsiveness
            
            if new_chunks:
                for chunk in new_chunks:
                    current_index += 1
                    yield {"data": chunk}
            
            # Check completion status
            state = await get_message_state(message_id)
            status = state.get("status")
            
            if status == "done":
                yield {"event": "done", "data": "Stream finished"}
                break
            
            if status == "error":
                error_msg = state.get("error", "Unknown error")
                yield {"event": "error", "data": error_msg}
                break

            # Small sleep if no new chunks (wait_for_stream_item already sleeps, but just in case)
            if not new_chunks:
                 await asyncio.sleep(0.1)

    return EventSourceResponse(event_generator())
