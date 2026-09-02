import redis

redis=redis.asyncio.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)