from fastapi import APIRouter, Request
from src.models import APIOutput
from src.utils.redis import enqueue_job
from src.utils import logger
from src.services.conversation_service import ConversationService
from src.models.conversations import ConversationCreate

router = APIRouter()

@router.post("/email/incoming")
async def handle_incoming_email(request: Request):
    try:
        raw_data = await request.json()
        logger.info(f"Incoming email webhook: {raw_data}")
        
        # Structure of raw_data from Node.js service:
        # { "event": "new_email", "data": { "id": "uuid", "sender_email": "...", "thread_id": "...", ... } }
        
        email_data = raw_data.get("data", {})
        email_id = email_data.get("id")
        thread_id = email_data.get("thread_id")
        subject = email_data.get("subject", "No Subject")
        
        if not email_id:
            return APIOutput.failure(message="Missing email ID")
            
        # Ensure conversation exists for this thread
        if thread_id:
            conv = ConversationService.find_by_metadata("email_thread_id", thread_id)
            if not conv:
                logger.info(f"Creating new conversation for email thread: {thread_id}")
                agent_name = "DatabaseAgent"
                # Use incoming subject or fallback to a spaced version of the agent name
                import re
                fallback_title = re.sub(r'([a-z])([A-Z])', r'\1 \2', agent_name).strip()
                conv_title = subject if subject and subject not in ["No Subject", "None", "null"] else fallback_title
                
                conv_create = ConversationCreate(
                    user_id=1, # Default user ID
                    agent=agent_name,
                    title=conv_title,
                    metadata={"email_thread_id": thread_id}
                )
                ConversationService.create_conversation(conv_create)
        
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
