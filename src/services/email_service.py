from typing import List, Optional
from src.utils.database import get_db_cursor
from src.models.messages import Message, EmailMessage

class EmailService:
    @staticmethod
    def get_message(id: str) -> Optional[EmailMessage]:
        query = """
            SELECT 
                id, 
                thread_id,
                sender_email,
                receiver_email,
                CASE WHEN sender_role = 'assistant' THEN 'assistant' ELSE 'user' END as role, 
                content,
                content_type,
                attachments,
                message_id,
                in_reply_to,
                timestamp
            FROM emails
            WHERE id = %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                # Find or create a conversation_id based on thread_id
                # For now, we assume thread_id could be mapped to conversation_id
                # Or we might need a mapping table.
                # In this project, conversations have an integer id.
                
                # Check for conversation mapping
                conv_query = "SELECT id FROM conversations WHERE metadata->>'email_thread_id' = %s LIMIT 1;"
                cursor.execute(conv_query, (row['thread_id'],))
                conv_row = cursor.fetchone()
                
                conversation_id = conv_row['id'] if conv_row else None
                
                return EmailMessage(
                    id=str(row['id']),
                    conversation_id=conversation_id,
                    role=row['role'],
                    content=row['content'],
                    sender_email=row['sender_email'],
                    receiver_email=row['receiver_email'],
                    thread_id=row['thread_id'],
                    timestamp=row['timestamp']
                )
            return None

    @staticmethod
    def get_messages_by_conversation_desc(conversation_id: int, limit: int = 20) -> List[Message]:
        # We need to find the thread_id for this conversation
        with get_db_cursor(commit=False) as cursor:
            cursor.execute("SELECT metadata->>'email_thread_id' as thread_id FROM conversations WHERE id = %s;", (conversation_id,))
            conv_row = cursor.fetchone()
            if not conv_row or not conv_row['thread_id']:
                return []
            
            thread_id = conv_row['thread_id']
            
            query = """
                SELECT 
                    id, 
                    CASE WHEN sender_role = 'assistant' THEN 'assistant' ELSE 'user' END as role, 
                    content,
                    timestamp
                FROM emails
                WHERE thread_id = %s
                ORDER BY timestamp DESC
                LIMIT %s;
            """
            cursor.execute(query, (thread_id, limit))
            rows = cursor.fetchall()
            return [Message(
                id=str(row['id']),
                conversation_id=conversation_id,
                role=row['role'],
                content=row['content'],
                timestamp=row['timestamp']
            ) for row in rows]
