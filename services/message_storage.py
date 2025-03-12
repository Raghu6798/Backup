import os
import json
from datetime import datetime
from database.redis_caching import redis_client
import motor.motor_asyncio

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["VMO"]
collection = db["chats"]

async def store_message(tenant_id: str, company_name: str, department: str, user_id: str, conversation_id: str, role: str, message: str):
    # Redis Key
    redis_key = f"{tenant_id}:{company_name}:{department}:{user_id}:{conversation_id}"

    # Message Data
    message_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "role": role,
        "message": message
    }

    # Store in Redis
    redis_client.lpush(redis_key, json.dumps(message_data))
    redis_client.ltrim(redis_key, 0, 9)  # Keep only the last 10 messages

    # Store in MongoDB
    await collection.update_one(
        {"userId": user_id},
        {
            "$setOnInsert": {  # Initialize the document if it doesn't exist
                "userId": user_id,
                "companyName": company_name,
                "department": department,
                "conversations": []  # Initialize the conversations array
            },
            "$push": {
                "conversations": {
                    "conversationId": conversation_id,
                    "messages": {
                        "query": message if role == "user" else None,
                        "answer": message if role == "assistant" else None,
                        "timestamp": message_data["timestamp"]
                    }
                }
            }
        },
        upsert=True  # Create the document if it doesn't exist
    )