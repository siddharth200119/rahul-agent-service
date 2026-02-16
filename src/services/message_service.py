from typing import List, Optional
import json
from src.utils.database import get_db_cursor
from src.models.messages import MessageCreate, MessageUpdate, Message, WhatsappMessage

class MessageService:
    @staticmethod
    def create_message(data: MessageCreate) -> Message:
        query = """
            INSERT INTO messages (conversation_id, role, content, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id, conversation_id, role, content, metadata, timestamp;
        """
        metadata_json = json.dumps(data.metadata) if data.metadata else None
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (data.conversation_id, data.role, data.content, metadata_json))
            row = cursor.fetchone()
            
            # Update conversation's last_message_at
            update_query = "UPDATE conversations SET last_message_at = NOW() WHERE id = %s;"
            cursor.execute(update_query, (data.conversation_id,))
            
            return Message(**row)

    @staticmethod
    def get_message(id: int) -> Optional[Message]:
        query = """
            SELECT id, from_number, conversation_id, role, content, metadata, timestamp
            FROM messages
            WHERE id = %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return WhatsappMessage(**row)
            return None

    @staticmethod
    def get_messages_by_conversation(conversation_id: int, limit: int = 50, offset: int = 0) -> List[Message]:
        query = """
            SELECT id, conversation_id, role, content, metadata, timestamp
            FROM messages
            WHERE conversation_id = %s
            ORDER BY timestamp ASC
            LIMIT %s OFFSET %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (conversation_id, limit, offset))
            rows = cursor.fetchall()
            return [Message(**row) for row in rows]

    @staticmethod
    def get_messages_by_conversation_desc(conversation_id: int, limit: int = 20) -> List[Message]:
        query = """
            SELECT id, conversation_id, role, content, metadata, timestamp
            FROM messages
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
        if data.content is not None:
            fields.append("content = %s")
            values.append(data.content)
        if data.metadata is not None:
            fields.append("metadata = %s")
            values.append(json.dumps(data.metadata))

        if not fields:
            return MessageService.get_message(id)

        values.append(id)
        query = f"""
            UPDATE messages
            SET {", ".join(fields)}
            WHERE id = %s
            RETURNING id, conversation_id, role, content, metadata, timestamp;
        """
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(values))
            row = cursor.fetchone()
            if row:
                return Message(**row)
            return None

    @staticmethod
    def delete_message(id: int) -> bool:
        query = "DELETE FROM messages WHERE id = %s;"
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (id,))
            return cursor.rowcount > 0
