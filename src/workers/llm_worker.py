import asyncio
import logging
import os
from src.utils.redis import claim_job, update_state, append_chunk, get_message_state
from src.services.message_service import MessageService
from src.models.messages import MessageUpdate
from dotenv import load_dotenv
import httpx

load_dotenv()

from src.utils import logger
import json

async def process_job(payload_data):
    # If your claim_job returns a string/JSON, parse it
    if isinstance(payload_data, str):
        data = json.loads(payload_data)
    else:
        data = payload_data

    message_id = data.get("message_id")
    message_type = data.get("message_type", "default") # 'whatsapp' or 'default'

    logger.info(f"Processing {message_type} message {message_id}")
    
    try:
        await update_state(message_id, "processing")
        
        # 1. Fetch Message using specific service
        if message_type == "whatsapp":
            from src.services.whatsapp_service import WhatsAppService
            assistant_msg = WhatsAppService.get_message(message_id)
            print(f"Assistantaas message {assistant_msg}")
        else:
            from src.services.message_service import MessageService
            assistant_msg = MessageService.get_message(message_id)

        if not assistant_msg:
            logger.error(f"Message {message_id} of type {message_type} not found")
            return

        # 2. Invoke Agent (Pass message_type down)
        from src.utils.invoke_agent import invoke_agent
        
        response_text = ""
        async for chunk in invoke_agent(assistant_msg.conversation_id, message_id, message_type):
            await append_chunk(message_id, chunk)
            response_text += chunk
    
        # Finalize & Persist
        await update_state(message_id, "done")
        
        update_data = MessageUpdate(content=response_text.strip(), metadata={"processed": True})
        
        if message_type == "whatsapp":
                
            node_api_url = f"{os.getenv('WHATSAPP_HOST', 'http://127.0.0.1:8080')}/send" 
            recipient_id = assistant_msg.group_id if assistant_msg.group_id else assistant_msg.from_number
            
            clean_recipient = recipient_id.split('@')[0] if recipient_id else None

            logger.info(f"Sending response to recipient: {recipient_id}")
            
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(node_api_url, json={
                        "number": assistant_msg.from_number, 
                        "message": response_text.strip() or "None",
                        "conversation_id": assistant_msg.conversation_id,
                        "group_id": recipient_id
                    })
                except Exception as e:
                    logger.error(f"Failed to notify Node service: {e}")
        else:
            MessageService.update_message(message_id, update_data)

    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}")
        await update_state(message_id, "error", error=str(e))

async def main():
    logger.info("Starting LLM Worker...")
    while True:
        try:
            message_id = await claim_job()
            
            if message_id:
                asyncio.create_task(process_job(message_id))
            else:
                # Wait a bit before polling again
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
