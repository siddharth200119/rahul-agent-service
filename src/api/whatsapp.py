from typing import List
from fastapi import APIRouter, HTTPException, Request
from src.models import APIOutput
# from src.models.whatsapp import WhatsAppMessageCreate, WhatsAppWebhookRegister
from src.services.whatsapp_service import WhatsAppService
from src.utils.redis import enqueue_job

router = APIRouter()

@router.post("/whatsapp/incoming")
async def handle_incoming_whatsapp(request: Request):
    try:
        raw_data = await request.json()
        print(raw_data)
        # Pass a payload with type and id
        job_payload = {
            "message_id": raw_data['id'],
            "message_type": "whatsapp"
        }
        print(f"Sending to redis: {job_payload}")
        await enqueue_job(job_payload) 
        
        return {"status": "received"}
    except Exception as e:
        return APIOutput.failure(message=str(e))