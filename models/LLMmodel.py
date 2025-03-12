from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os        
load_dotenv()

def get_LLM():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.4
    )
