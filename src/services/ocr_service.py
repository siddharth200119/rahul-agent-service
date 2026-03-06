from typing import List, Optional, Dict, Any
from src.utils.database import get_db_cursor, get_db_config
from src.utils import logger
import json

class OCRService:
    @staticmethod
    def add_to_queue(filepath: str, json_schema: Dict[str, Any], priority: str) -> int:
        # Map priority string to integer
        priority_map = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
        priority_val = priority_map.get(priority.lower(), 1)

        query = """
        INSERT INTO ocr_queue (filepath, json_schema, priority, status)
        VALUES (%s, %s, %s, 'pending')
        RETURNING id;
        """
        with get_db_cursor(commit=True, db_config=get_db_config()) as cursor:
            cursor.execute(query, (filepath, json.dumps(json_schema), priority_val))
            result = cursor.fetchone()
            return result['id']

    @staticmethod
    def get_task_status(task_id: int) -> Optional[Dict[str, Any]]:
        query = """
        SELECT id, filepath, json_schema, status, priority, result, created_at
        FROM ocr_queue
        WHERE id = %s;
        """
        with get_db_cursor(db_config=get_db_config()) as cursor:
            cursor.execute(query, (task_id,))
            return cursor.fetchone()

    @staticmethod
    def get_next_task() -> Optional[Dict[str, Any]]:
        """
        Fetches the next pending task based on priority and creation time.
        Updates status to 'worker assigned' atomically.
        """
        # Using FOR UPDATE SKIP LOCKED for concurrent workers
        query = """
        UPDATE ocr_queue
        SET status = 'worker assigned'
        WHERE id = (
            SELECT id
            FROM ocr_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING id, filepath, json_schema, priority, status;
        """
        with get_db_cursor(commit=True, log_queries=False, db_config=get_db_config()) as cursor:
            cursor.execute(query)
            return cursor.fetchone()

    @staticmethod
    def update_task_result(task_id: int, result: Dict[str, Any], status: str = 'done'):
        query = """
        UPDATE ocr_queue
        SET result = %s, status = %s
        WHERE id = %s;
        """
        with get_db_cursor(commit=True, db_config=get_db_config()) as cursor:
            cursor.execute(query, (json.dumps(result), status, task_id))

    @staticmethod
    def update_task_status(task_id: int, status: str):
        query = """
        UPDATE ocr_queue
        SET status = %s
        WHERE id = %s;
        """
        with get_db_cursor(commit=True, db_config=get_db_config()) as cursor:
            cursor.execute(query, (status, task_id))
