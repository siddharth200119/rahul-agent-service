"""
ocr_queue
"""

from yoyo import step

__depends__ = {'20260213_01_analysis_tables'}

steps = [
    step(
        """
        CREATE TABLE ocr_queue (
            id BIGSERIAL PRIMARY KEY,
            filepath TEXT NOT NULL,
            json_schema JSONB,
            status VARCHAR(50) DEFAULT 'pending',
            priority INTEGER DEFAULT 0,
            result JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        "DROP TABLE IF EXISTS ocr_queue;"
    )
]
