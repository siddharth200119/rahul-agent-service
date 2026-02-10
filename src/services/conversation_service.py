from typing import List, Optional
from src.utils.database import get_db_cursor
from src.models.conversations import ConversationCreate, ConversationUpdate, Conversation

class ConversationService:
    @staticmethod
    def create_conversation(data: ConversationCreate) -> Conversation:
        query = """
            INSERT INTO conversations (user_id, agent, title)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, agent, title, created_at, last_message_at;
        """
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (data.user_id, data.agent, data.title))
            row = cursor.fetchone()
            return Conversation(**row)

    @staticmethod
    def get_conversation(id: int) -> Optional[Conversation]:
        query = """
            SELECT id, user_id, agent, title, created_at, last_message_at
            FROM conversations
            WHERE id = %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (id,))
            row = cursor.fetchone()
            if row:
                return Conversation(**row)
            return None

    @staticmethod
    def get_conversations(user_id: int, limit: int = 10, offset: int = 0) -> List[Conversation]:
        query = """
            SELECT id, user_id, agent, title, created_at, last_message_at
            FROM conversations
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s;
        """
        with get_db_cursor(commit=False) as cursor:
            cursor.execute(query, (user_id, limit, offset))
            rows = cursor.fetchall()
            return [Conversation(**row) for row in rows]

    @staticmethod
    def update_conversation(id: int, data: ConversationUpdate) -> Optional[Conversation]:
        # Build dynamic query based on provided fields
        fields = []
        values = []
        if data.title is not None:
            fields.append("title = %s")
            values.append(data.title)
        if data.agent is not None:
            fields.append("agent = %s")
            values.append(data.agent)

        if not fields:
            return ConversationService.get_conversation(id)

        values.append(id)
        query = f"""
            UPDATE conversations
            SET {", ".join(fields)}
            WHERE id = %s
            RETURNING id, user_id, agent, title, created_at, last_message_at;
        """
        
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(values))
            row = cursor.fetchone()
            if row:
                return Conversation(**row)
            return None

    @staticmethod
    def delete_conversation(id: int) -> bool:
        query = "DELETE FROM conversations WHERE id = %s;"
        with get_db_cursor(commit=True) as cursor:
            cursor.execute(query, (id,))
            return cursor.rowcount > 0
