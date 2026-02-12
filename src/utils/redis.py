import os
import json
import asyncio
from typing import Dict, Optional, Any
from redis.asyncio import Redis
from src.utils import logger

# -------------------------
# Config
# -------------------------

def get_redis_config():
    return {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", 6379)),
        "db": int(os.getenv("REDIS_DB", 0)),
        "decode_responses": True,
    }


# -------------------------
# Client singleton
# -------------------------

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis

    if _redis is None:
        cfg = get_redis_config()
        logger.info(f"Connecting to Redis {cfg['host']}:{cfg['port']}/{cfg['db']}")

        _redis = Redis(**cfg)

        # Health check
        await _redis.ping()
        logger.info("Redis connection established")

    return _redis


# -------------------------
# Streaming / Queue Helpers
# -------------------------

QUEUE_KEY = "llm_work_queue"
STATE_KEY_PREFIX = "message:{}:{}:state"
STREAM_KEY_PREFIX = "message:{}:{}:stream"
TTL_SECONDS = 3600  # 1 hour


async def enqueue_job(payload: Dict[str, Any]):
    """
    Push payload (id and type) to work queue and init state
    Example payload: {"message_id": 10, "message_type": "whatsapp"}
    """
    r = await get_redis()
    
    msg_id = payload.get("message_id")
    msg_type = payload.get("message_type", "default")
    
    # Init state using the new type-aware prefix
    state_key = STATE_KEY_PREFIX.format(msg_type, msg_id)
    
    await r.hset(state_key, mapping={
        "status": "pending",
        "message_type": msg_type,
        "created_at": str(asyncio.get_event_loop().time())
    })
    await r.expire(state_key, TTL_SECONDS)

    # Push the whole JSON payload to the queue
    payload_json = json.dumps(payload)
    logger.info(f"Enqueuing {msg_type} job: {msg_id}")
    await r.rpush(QUEUE_KEY, payload_json)


async def claim_job() -> Optional[Dict[str, Any]]:
    """
    Worker calls this to get next job payload
    """
    r = await get_redis()
    result = await r.blpop(QUEUE_KEY, timeout=5)
    
    if result:
        # result[1] is the JSON string
        return json.loads(result[1])
    return None

async def update_state(message_id: int, status: str, message_type: str = "default", **kwargs):
    """
    Update status using type-aware keys
    """
    r = await get_redis()
    state_key = STATE_KEY_PREFIX.format(message_type, message_id)
    mapping = {"status": status}
    mapping.update(kwargs)
    await r.hset(state_key, mapping=mapping)
    await r.expire(state_key, TTL_SECONDS)


async def append_chunk(message_id: int, chunk: str, message_type: str = "default"):
    """
    Append text chunk to type-aware stream list
    """
    r = await get_redis()
    stream_key = STREAM_KEY_PREFIX.format(message_type, message_id)
    await r.rpush(stream_key, chunk)
    await r.expire(stream_key, TTL_SECONDS)


async def get_message_state(message_id: int, message_type: str = "default") -> dict:
    r = await get_redis()
    state_key = STATE_KEY_PREFIX.format(message_type, message_id)
    return await r.hgetall(state_key)


async def get_stream_history(message_id: int, message_type: str = "default") -> list[str]:
    r = await get_redis()
    stream_key = STREAM_KEY_PREFIX.format(message_type, message_id)
    return await r.lrange(stream_key, 0, -1)


async def wait_for_stream_item(message_id: int, start_index: int, timeout: int = 20, message_type: str = "default") -> list[str]:
    """
    Wait for new items in the stream.
    Since Redis Lists don't support blocking read from specific index,
    we have to poll or use Pub/Sub.
    For simplicity and reliability, we will POLL here with short sleep.
    """
    r = await get_redis()
    stream_key = STREAM_KEY_PREFIX.format(message_type, message_id)
    
    end_time = asyncio.get_event_loop().time() + timeout
    
    while asyncio.get_event_loop().time() < end_time:
        # Check if we have data beyond start_index
        # LLEN gives total count. Index is 0-based.
        # If start_index == 0, we want element 0.
        # If length is 5, valid indices are 0-4. Next write is 5.
        
        length = await r.llen(stream_key)
        if length > start_index:
            # We have new data
            # LRANGE from start_index to end
            return await r.lrange(stream_key, start_index, -1)
        
        # Check if processing is done/error to stop waiting
        state = await get_message_state(message_id, message_type=message_type)
        if state.get("status") in ["done", "error"] and length <= start_index:
            return []
            
        await asyncio.sleep(0.5)
        
    return []
