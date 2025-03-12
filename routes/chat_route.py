from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter
import os
from models.LLMmodel import get_LLM
from database.qdrant_store import get_qdrant_store
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from uuid import uuid4
from services.message_storage import store_message  
from database.redis_caching import redis_client  

router = APIRouter()

# Initialize Gemini LLM
gemini_2 = get_LLM()

# Define the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """ 
    You are an AI assistant specialized in vendor contract management. 
    Answer the given question **only** using the retrieved context: {context}. 
    Do not use external knowledge. If the context does not contain an answer, state: 
    'The provided contract does not contain this information.'

    Extract structured details such as:
    - Vendor Name(s) 
    - Contract Duration 
    - Payment Terms 
    - Responsibilities of each party 
    - Penalties, Dispute Resolution, and Termination Clauses  
    - Any relevant regulations or tax information 

    Ensure the response is:
    - **Concise yet detailed**  
    - **Well-structured with bullet points or tables**  
    - **Strictly based on the document**  

    If the question requires calculations (e.g., billing amounts, tax implications), provide a step-by-step breakdown. 
    """),
    MessagesPlaceholder(variable_name="chat_history"), 
    ("human", "{question}")
])

chat_chain = prompt | gemini_2 | StrOutputParser()


chat_with_history = RunnableWithMessageHistory(
    chat_chain,
    lambda session_id: MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string=os.getenv("MONGO_URI"),
        database_name="VMO",
        collection_name="chat_histories",
    ),
    input_messages_key="question",
    history_messages_key="chat_history"  # Key matches the placeholder
)

@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid4())  # Generate a unique session ID for each WebSocket connection

    try:
        while True:
            # Receive the user's question
            question = await websocket.receive_text()

            # Exit condition
            if question.lower() in ["quit", "exit", ""]:
                await websocket.send_text("Chat session ended. Goodbye!")
                break

            # Retrieve relevant documents from Qdrant
            qdrant = get_qdrant_store()
            retriever = qdrant.as_retriever(search_kwargs={"k": 2})
            context = "\n".join(doc.page_content for doc in retriever.get_relevant_documents(question))

            # Generate a response using the chat chain
            response = chat_with_history.invoke(
                {"question": question, "context": context},
                config={"configurable": {"session_id": session_id}}
            )

            # Store the user's question and the assistant's response in Redis
            await store_message(
                tenant_id="tenant1",
                company_name="companyA",
                department="sales",
                user_id="user123",
                conversation_id=session_id,
                role="user",
                message=question
            )
            await store_message(
                tenant_id="tenant1",
                company_name="companyA",
                department="sales",
                user_id="user123",
                conversation_id=session_id,
                role="assistant",
                message=response
            )

            # Send the response back to the client
            await websocket.send_text(response)

    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")