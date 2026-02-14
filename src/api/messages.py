from typing import List
from fastapi import APIRouter, Query, HTTPException
from src.models import APIOutput
from src.models.messages import Message, MessageCreate, MessageUpdate
from src.services.message_service import MessageService

router = APIRouter()

@router.post("/conversations/{conversation_id}/messages", response_model=APIOutput[Message])
async def create_message(conversation_id: int, data: MessageCreate):
    try:
        if data.conversation_id != conversation_id:
             return APIOutput.failure(message="Conversation ID mismatch", status_code=400)
             
        # 1. Create User Message
        user_msg = MessageService.create_message(data)
        
        # 2. Create Placeholder Assistant Message
        assistant_data = MessageCreate(
            conversation_id=conversation_id,
            role="assistant",
            content="", # Empty content initially
            metadata={"status": "pending"}
        )
        assistant_msg = MessageService.create_message(assistant_data)
        
        # 3. Enqueue Job for Worker
        from src.utils.redis import enqueue_job
        await enqueue_job({
            "message_id": assistant_msg.id,
            "message_type": "default"
        })
        
        # 4. Return Assistant Message (so client can subscribe to its ID)
        return APIOutput.success(data=assistant_msg, status_code=201)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.get("/conversations/{conversation_id}/messages", response_model=APIOutput[List[Message]])
def get_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    try:
        messages = MessageService.get_messages_by_conversation(conversation_id, limit, offset)
        return APIOutput.success(data=messages)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.get("/messages/{id}", response_model=APIOutput[Message])
def get_message(id: int):
    try:
        message = MessageService.get_message(id)
        if not message:
            return APIOutput.failure(message="Message not found", status_code=404)
        return APIOutput.success(data=message)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.put("/messages/{id}", response_model=APIOutput[Message])
def update_message(id: int, data: MessageUpdate):
    try:
        message = MessageService.update_message(id, data)
        if not message:
            return APIOutput.failure(message="Message not found", status_code=404)
        return APIOutput.success(data=message)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.delete("/messages/{id}", response_model=APIOutput[None])
def delete_message(id: int):
    try:
        success = MessageService.delete_message(id)
        if not success:
            return APIOutput.failure(message="Message not found", status_code=404)
        return APIOutput.success(message="Message deleted successfully")
    except Exception as e:
        return APIOutput.failure(message=str(e))
