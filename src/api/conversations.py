from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from src.models import APIOutput
from src.models.conversations import Conversation, ConversationCreate, ConversationUpdate
from src.services.conversation_service import ConversationService

router = APIRouter()

@router.post("/conversations", response_model=APIOutput[Conversation])
def create_conversation(data: ConversationCreate):
    try:
        conversation = ConversationService.create_conversation(data)
        return APIOutput.success(data=conversation, status_code=201)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.get("/conversations/{id}", response_model=APIOutput[Conversation])
def get_conversation(id: int):
    conversation = ConversationService.get_conversation(id)
    if not conversation:
        return APIOutput.failure(message="Conversation not found", status_code=404)
    return APIOutput.success(data=conversation)

@router.get("/conversations", response_model=APIOutput[List[Conversation]])
def get_conversations(
    user_id: int = Query(..., description="User ID to filter conversations"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    try:
        conversations = ConversationService.get_conversations(user_id, limit, offset)
        return APIOutput.success(data=conversations)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.put("/conversations/{id}", response_model=APIOutput[Conversation])
def update_conversation(id: int, data: ConversationUpdate):
    try:
        conversation = ConversationService.update_conversation(id, data)
        if not conversation:
            return APIOutput.failure(message="Conversation not found", status_code=404)
        return APIOutput.success(data=conversation)
    except Exception as e:
        return APIOutput.failure(message=str(e))

@router.delete("/conversations/{id}", response_model=APIOutput[None])
def delete_conversation(id: int):
    try:
        success = ConversationService.delete_conversation(id)
        if not success:
            return APIOutput.failure(message="Conversation not found", status_code=404)
        return APIOutput.success(message="Conversation deleted successfully")
    except Exception as e:
        return APIOutput.failure(message=str(e))
