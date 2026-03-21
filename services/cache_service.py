import hashlib
import json
from typing import Any

from core.redis_client import redis_client


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower()


def make_hash_key(data: dict[str, Any]) -> str:
    raw = json.dumps(
        data,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_json_cache(key: str):
    cached = redis_client.get(key)
    if not cached:
        return None
    return json.loads(cached)


def set_json_cache(key: str, value: Any, ttl: int):
    redis_client.setex(
        key,
        ttl,
        json.dumps(value, ensure_ascii=False),
    )


def register_group_key(group_key: str, cache_key: str, ttl: int | None = None):
    pipe = redis_client.pipeline()
    pipe.sadd(group_key, cache_key)
    if ttl:
        pipe.expire(group_key, ttl)
    pipe.execute()


def delete_group_keys(group_key: str):
    keys = list(redis_client.smembers(group_key))
    if keys:
        redis_client.delete(*keys)
    redis_client.delete(group_key)