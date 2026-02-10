"""
messages
"""

from yoyo import step

__depends__ = {'20260210_01_k5Yuv-conversations'}

steps = [
    step(
        """
        CREATE TABLE messages (
            id BIGSERIAL PRIMARY KEY,
            conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            role VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB
        );

        CREATE INDEX idx_messages_conversation_id
            ON messages (conversation_id);
        """,
        """
        DROP TABLE IF EXISTS messages;
        """
    )
]
