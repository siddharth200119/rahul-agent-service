from typing import List, Optional
import json
from src.utils.database import get_db_cursor
from src.models.messages import MessageCreate, MessageUpdate, Message, WhatsappMessage

class WhatsAppService:
    @staticmethod
    def get_message(id: int) -> Optional[WhatsappMessage]:
        # Added group_id to the SELECT statement
        query = """
            SELECT 
                id, 
                conversation_id, 
                CASE WHEN is_from_me THEN 'assistant' ELSE 'user' END as role, 
                body as content, 
                NULL as metadata, 
                from_number,
                group_id,
                timestamp
            FROM whatsapp_messages
            WHERE id = %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                # Ensure your WhatsappMessage Pydantic model has group_id: Optional[str]
                return WhatsappMessage(**row)
            return None

    @staticmethod
    def get_messages_by_conversation_desc(conversation_id: int, limit: int = 20) -> List[Message]:
        # Includes group_id so the LLM context knows the source if needed
        query = """
            SELECT 
                id, 
                conversation_id, 
                CASE WHEN is_from_me THEN 'assistant' ELSE 'user' END as role, 
                body as content, 
                NULL as metadata,
                from_number,
                group_id,
                timestamp
            FROM whatsapp_messages
            WHERE conversation_id = %s
            ORDER BY timestamp DESC
            LIMIT %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (conversation_id, limit))
            rows = cursor.fetchall()
            return [Message(**row) for row in rows]

    @staticmethod
    def update_message(id: int, data: MessageUpdate) -> Optional[dict]:
        fields = []
        values = []
        
        if data.content is not None:
            fields.append("body = %s")
            values.append(data.content)
            
        # If you ever want to update group_id via this service, add logic here

        if not fields:
            return WhatsAppService.get_message(id)

        values.append(id)
        # Added group_id to the RETURNING clause
        query = f"""
            UPDATE whatsapp_messages
            SET {", ".join(fields)}
            WHERE id = %s
            RETURNING 
                id, 
                conversation_id, 
                CASE WHEN is_from_me THEN 'assistant' ELSE 'user' END as role, 
                body as content, 
                NULL as metadata, 
                from_number,
                group_id,
                timestamp;
        """
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(values))
            row = cursor.fetchone()
            if row:
                return row
            return None

    @staticmethod
    def delete_message(id: int) -> bool:
        query = "DELETE FROM whatsapp_messages WHERE id = %s;"
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (id,))
            return cursor.rowcount > 0