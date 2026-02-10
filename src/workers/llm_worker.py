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
        
        # Simulate LLM Generation
        response_text = ""
        mock_response = "Hello! This is a streamed response from the LLM worker. I am generating this text chunk by chunk to demonstrate the streaming capability."
        
        chunks = mock_response.split(" ")
        for i, word in enumerate(chunks):
            chunk = word + " "
            await append_chunk(message_id, chunk)
            response_text += chunk
            # Simulate latency
            await asyncio.sleep(0.2)
            
        # Finalize
        await update_state(message_id, "done")
        
        # Persist to DB
        logger.info(f"Persisting message {message_id} to DB")
        from src.services.message_service import MessageService # Import here to avoid circulars if any
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
