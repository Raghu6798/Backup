import os
import json
from database.redis_caching import redis_client
import motor.motor_asyncio

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["VMO"]
collection = db["chats"]

async def get_messages(tenant_id: str, company_name: str, department: str, user_id: str, conversation_id: str):
    # Redis Key
    redis_key = f"{tenant_id}:{company_name}:{department}:{user_id}:{conversation_id}"

    # Fetch from Redis
    recent_messages = redis_client.lrange(redis_key, 0, -1)
    recent_messages = [json.loads(msg) for msg in recent_messages]

    if len(recent_messages) < 10:  # If Redis doesn't have enough messages
        # Fetch historical messages from MongoDB
        user_data = await collection.find_one(
            {"userId": user_id},
            {"conversations": {"$elemMatch": {"conversationId": conversation_id}}}
        )
        if user_data and user_data.get("conversations"):
            historical_messages = user_data["conversations"][0].get("messages", [])
            historical_messages = [
                {
                    "timestamp": msg["timestamp"],
                    "role": "user" if msg.get("query") else "assistant",
                    "message": msg.get("query") or msg.get("answer")
                }
                for msg in historical_messages
            ]
            # Cache historical messages in Redis
            for msg in historical_messages:
                redis_client.lpush(redis_key, json.dumps(msg))
            redis_client.ltrim(redis_key, 0, 9)
            return historical_messages

    return recent_messages