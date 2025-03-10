import os
from os import getenv

from redis.asyncio import Redis
from dotenv import load_dotenv

load_dotenv()

redis_port = int(os.getenv('REDIS_PORT'))
redis_host = os.getenv('REDIS_HOST')

redis_client = Redis(host=redis_host, port=redis_port, decode_responses=True)


async def init_redis():
    global redis_client
    redis_client = Redis(
        host=redis_host, 
        port=redis_port, 
        decode_responses=True
    )
    return redis_client


async def close_redis():
    await redis_client.close()
