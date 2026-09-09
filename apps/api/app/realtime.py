from __future__ import annotations

import json
import logging
import os
from typing import Any
from uuid import UUID

import redis.asyncio as redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_client: redis.Redis | None = None


def kitchen_channel(restaurant_id: UUID) -> str:
    return f"kitchen:{restaurant_id}"


async def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def publish_kitchen_event(restaurant_id: UUID, payload: dict[str, Any]) -> None:
    """Best-effort publish — order/status must not fail if Redis is down."""
    try:
        client = await get_redis()
        await client.publish(kitchen_channel(restaurant_id), json.dumps(payload))
    except Exception:
        logger.exception("kitchen publish failed for restaurant %s", restaurant_id)
