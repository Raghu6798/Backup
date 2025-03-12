from fastapi import APIRouter
from models.LLMmodel import get_LLM
from pydantic import BaseModel
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import StrOutputParser
from uuid import uuid4
from database.qdrant_store import get_qdrant_store

router = APIRouter()
gemini_2 = get_LLM()

store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

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
    chat_chain, get_session_history,
    input_messages_key="question",
    history_messages_key="chat_history"
)

class QueryRequest(BaseModel):
    question: str

def retrieve_documents(query: str):
    qdrant = get_qdrant_store()
    retriever = qdrant.as_retriever(search_kwargs={"k": 2})
    return retriever.get_relevant_documents(query)

@router.post("/query/")
async def query_rag(request: QueryRequest):
    question = request.question  # Extract `question` from JSON
    session_id = str(uuid4())
    context = retrieve_documents(question)
    print("\n--- Retrieved Context ---\n", context, "\n-------------------------\n")
    response = chat_with_history.invoke(
        {"question": question, "context": context},
        config={"configurable": {"session_id": session_id}}
    )
    
    return {"response": response}