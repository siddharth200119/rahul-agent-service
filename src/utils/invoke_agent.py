import os
from dotenv import load_dotenv
from typing import AsyncGenerator

from src.utils import logger
from src.services.message_service import MessageService
from src.services.conversation_service import ConversationService

# Load environment variables
load_dotenv()

# Import from new agentic structure
from src.agentic.agents.test_agent import get_test_agent
from RAW.modals import Message

async def invoke_agent(conversation_id: int, message_id: int) -> AsyncGenerator[str, None]:
    """
    Invokes the agent for a given conversation using the refactored agentic structure.
    """
    # 1. Fetch Conversation Details
    conversation = ConversationService.get_conversation(conversation_id)
    if not conversation:
        logger.error(f"Conversation {conversation_id} not found")
        return

    agent_name = conversation.agent or "Agent"

    # 2. Fetch History (DESC order) and User Input
    desc_history = MessageService.get_messages_by_conversation_desc(conversation_id, limit=20)
    full_history = sorted(desc_history, key=lambda m: m.timestamp)
    
    # Filter out the current assistant placeholder
    valid_msgs = [m for m in full_history if m.id != message_id]
    
    raw_history = []
    user_input = None
    
    if valid_msgs:
        last_msg = valid_msgs[-1]
        if last_msg.role == 'user':
            user_input = last_msg.content
            history_msgs = valid_msgs[:-1]
        else:
            # If the last message isn't user, we might have an issue or this is a system trigger
            logger.warning(f"Last message {last_msg.id} is not user role: {last_msg.role}")
            # For now, we abort if no user input found to drive the agent
            yield "Error: No user input found."
            return
    else:
        yield "Error: No message history found (user input missing)."
        return
        
    # Convert to RAW Messages
    for msg in history_msgs:
        raw_history.append(Message(role=msg.role, content=msg.content))

    logger.debug(f"--- Invoking Agent: {agent_name} ---")
    logger.debug(f"History Length: {len(raw_history)}")

    # 3. Initialize Agent using Factory
    # Future: We might select different agents based on `agent_name`
    # For now, we use the test agent structure but pass the dynamic name
    try:
        agent = get_test_agent(user_id=conversation.user_id, history=raw_history)
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        yield f"Error initializing agent: {str(e)}"
        return

    # 4. Stream Response
    async for chunk in agent(user_input, stream=True):
        if isinstance(chunk, dict) and "content" in chunk:
            content_obj = chunk["content"]
            
            if isinstance(content_obj, dict) and "content" in content_obj:
                text_content = content_obj["content"]
                if text_content:
                    yield text_content
            
            elif isinstance(content_obj, str):
                pass
