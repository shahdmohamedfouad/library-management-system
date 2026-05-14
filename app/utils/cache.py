# app/core/cache.py
import json
from redis import Redis
from functools import wraps
import asyncio

redis_client = Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3
)


def cache(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                key = f"cache:{func.__name__}:{str(args)}:{str(kwargs)}"
                cached = redis_client.get(key)
                if cached:
                    return json.loads(cached)

                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                redis_client.setex(key, ttl, json.dumps(result, default=str))
                return result
            except Exception as e:
                print(f"Redis cache error: {e}")
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Cache Invalidation Functions
def invalidate_book_cache(book_id=None):
    try:
        if book_id:
            redis_client.delete(f"cache:get_book:*{book_id}*")
        redis_client.delete("cache:get_books*")  # Invalidate list
    except:
        pass
