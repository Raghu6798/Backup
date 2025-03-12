import os
from dotenv import load_dotenv
from langchain_redis import RedisSemanticCache
import redis

load_dotenv()

redis_client = redis.Redis(
    host=os.getenv('REDIS_URL'),
    port=os.getenv("REDIS_PORT"),
    decode_responses=True,
    username="default",
    password=os.getenv("REDIS_PASSWORD"),
)