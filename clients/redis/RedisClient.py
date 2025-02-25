import os
from os import getenv

import redis
from dotenv import load_dotenv

load_dotenv()

redis_port = int(os.getenv('REDIS_PORT'))
redis_host = os.getenv('REDIS_HOST')

redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
