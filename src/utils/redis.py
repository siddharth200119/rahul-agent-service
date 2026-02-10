import os
import json
import asyncio
from contextlib import asynccontextmanager
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
STATE_KEY_PREFIX = "message:{}:state"
STREAM_KEY_PREFIX = "message:{}:stream"
TTL_SECONDS = 3600  # 1 hour

async def enqueue_job(message_id: int):
    """
    Push message_id to work queue and init state
    """
    r = await get_redis()
    
    # Init state
    state_key = STATE_KEY_PREFIX.format(message_id)
    await r.hset(state_key, mapping={
        "status": "pending",
        "created_at": str(asyncio.get_event_loop().time())
    })
    await r.expire(state_key, TTL_SECONDS)

    # Push to queue (LIF0 or FIFO - LPUSH/RPOP usually FIFO)
    # We'll use RPUSH so workers BLPOP from left (FIFO) or vice versa
    await r.rpush(QUEUE_KEY, message_id)


async def claim_job() -> int | None:
    """
    Worker calls this to get next job (non-blocking for demo, or blocking)
    """
    r = await get_redis()
    # BLPOP returns (key, value) tuple
    result = await r.blpop(QUEUE_KEY, timeout=5)
    if result:
        return int(result[1])
    return None


async def update_state(message_id: int, status: str, **kwargs):
    """
    Update status (processing, done, error) and other metadata
    """
    r = await get_redis()
    state_key = STATE_KEY_PREFIX.format(message_id)
    mapping = {"status": status}
    mapping.update(kwargs)
    await r.hset(state_key, mapping=mapping)
    # Reset TTL on activity
    await r.expire(state_key, TTL_SECONDS)


async def append_chunk(message_id: int, chunk: str):
    """
    Append text chunk to stream list
    """
    r = await get_redis()
    stream_key = STREAM_KEY_PREFIX.format(message_id)
    await r.rpush(stream_key, chunk)
    await r.expire(stream_key, TTL_SECONDS)


async def get_stream_history(message_id: int) -> list[str]:
    """
    Get all chunks so far
    """
    r = await get_redis()
    stream_key = STREAM_KEY_PREFIX.format(message_id)
    # LRANGE 0 -1 gets everything
    return await r.lrange(stream_key, 0, -1)


async def get_message_state(message_id: int) -> dict:
    r = await get_redis()
    state_key = STATE_KEY_PREFIX.format(message_id)
    return await r.hgetall(state_key)


async def wait_for_stream_item(message_id: int, start_index: int, timeout: int = 20) -> list[str]:
    """
    Wait for new items in the stream.
    Since Redis Lists don't support blocking read from specific index,
    we have to poll or use Pub/Sub.
    For simplicity and reliability, we will POLL here with short sleep.
    """
    r = await get_redis()
    stream_key = STREAM_KEY_PREFIX.format(message_id)
    
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
        state = await get_message_state(message_id)
        if state.get("status") in ["done", "error"] and length <= start_index:
            return []
            
        await asyncio.sleep(0.5)
        
    return []
