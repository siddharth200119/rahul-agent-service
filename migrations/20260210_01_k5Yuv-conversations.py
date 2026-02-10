from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        CREATE TABLE conversations (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            agent VARCHAR(100) NOT NULL,
            title VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_message_at TIMESTAMPTZ
        );

        CREATE INDEX idx_conversations_user_id
            ON conversations (user_id);

        CREATE INDEX idx_conversations_last_message_at
            ON conversations (last_message_at);
        """,
        """
        DROP TABLE IF EXISTS conversations;
        """
    )
]
