from fastapi import APIRouter, Request
from src.models import APIOutput
from src.utils.redis import enqueue_job
from src.utils import logger

router = APIRouter()

@router.post("/email/incoming")
async def handle_incoming_email(request: Request):
    try:
        raw_data = await request.json()
        logger.info(f"Incoming email webhook: {raw_data}")
        
        # Structure of raw_data from Node.js service:
        # { "event": "new_email", "data": { "id": "uuid", "sender_email": "...", ... } }
        
        email_data = raw_data.get("data", {})
        email_id = email_data.get("id")
        
        if not email_id:
            return APIOutput.failure(message="Missing email ID")
            
        job_payload = {
            "message_id": email_id,
            "message_type": "email"
        }
        
        logger.info(f"Enqueuing email job: {job_payload}")
        await enqueue_job(job_payload) 
        
        return {"status": "received", "job_enqueued": True}
    except Exception as e:
        logger.error(f"Error handling incoming email: {e}")
        return APIOutput.failure(message=str(e))
