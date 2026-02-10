import asyncio
import logging
from src.utils.redis import claim_job, update_state, append_chunk, get_message_state
from src.services.message_service import MessageService
from src.models.messages import MessageUpdate
from dotenv import load_dotenv

load_dotenv()

from src.utils import logger

async def process_job(message_id: int):
    logger.info(f"Processing message {message_id}")
    
    try:
        await update_state(message_id, "processing")
        
        # 1. Fetch Assistant Message for Conversation ID
        from src.services.message_service import MessageService
        assistant_msg = MessageService.get_message(message_id)
        if not assistant_msg:
            logger.error(f"Message {message_id} not found")
            return

        # 2. Invoke Agent & Stream
        from src.utils.invoke_agent import invoke_agent
        
        response_text = ""
        async for chunk in invoke_agent(assistant_msg.conversation_id, message_id):
             await append_chunk(message_id, chunk)
             response_text += chunk
        
        # Finalize
        await update_state(message_id, "done")
        
        # Persist to DB
        logger.info(f"Persisting message {message_id} to DB")
        # The message ID here is the ASSISTANT message ID that was created as a placeholder
        # We just need to update its content
        
        update_data = MessageUpdate(content=response_text.strip(), metadata={"processed": True})
        MessageService.update_message(message_id, update_data)
        
        logger.info(f"Finished processing message {message_id}")

    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}")
        await update_state(message_id, "error", error=str(e))
        
        # Persist error to DB
        try:
             update_data = MessageUpdate(content=f"Error: {str(e)}", metadata={"error": True})
             MessageService.update_message(message_id, update_data)
        except Exception as db_e:
            logger.error(f"Failed to persist error state: {db_e}")

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
