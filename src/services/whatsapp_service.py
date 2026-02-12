from typing import List, Optional
import json
from src.utils.database import get_db_cursor
from src.models.messages import MessageCreate, MessageUpdate, Message, WhatsappMessage

class WhatsAppService:
    @staticmethod
    def get_message(id: int) -> Optional[Message]:
        # Maps whatsapp_messages columns to the standard Message model
        query = """
            SELECT 
                id, 
                conversation_id, 
                CASE WHEN is_from_me THEN 'assistant' ELSE 'user' END as role, 
                body as content, 
                NULL as metadata, 
                from_number ,
                timestamp
            FROM whatsapp_messages
            WHERE id = %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return WhatsappMessage(**row)
            return None

    @staticmethod
    def get_messages_by_conversation_desc(conversation_id: int, limit: int = 20) -> List[Message]:
        query = """
            SELECT 
                id, 
                conversation_id, 
                CASE WHEN is_from_me THEN 'assistant' ELSE 'user' END as role, 
                body as content, 
                NULL as metadata, 
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
    def update_message(id: int, data: MessageUpdate) -> Optional[Message]:
        fields = []
        values = []
        
        # Mapping standard 'content' update to WhatsApp 'body' column
        if data.content is not None:
            fields.append("body = %s")
            values.append(data.content)
            
        # If your whatsapp_messages table doesn't have a metadata column yet, 
        # we skip data.metadata or you can add it via migration.

        if not fields:
            return WhatsAppService.get_message(id)

        values.append(id)
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
                timestamp;
        """
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(values))
            row = cursor.fetchone()
            if row:
                # Update conversation's last_activity (optional but recommended)
                # cursor.execute(
                #     "UPDATE conversations SET last_message_at = NOW() WHERE id = %s;",
                #     (row['conversation_id'],)
                # )
                return row
            return None

    @staticmethod
    def delete_message(id: int) -> bool:
        query = "DELETE FROM whatsapp_messages WHERE id = %s;"
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (id,))
            return cursor.rowcount > 0