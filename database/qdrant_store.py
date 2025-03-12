import os
from langchain_qdrant import QdrantVectorStore
from models.embedding_model import get_embedding_model
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_qdrant_store():
    """Initialize Qdrant and return the retriever."""
    url = os.getenv("QDRANT_URI")
    api_key = os.getenv("QDRANT_API_KEY")
    qdrant = QdrantVectorStore.from_documents(
        documents=[],
        embedding=get_embedding_model(),
        url=url,
        prefer_grpc=True,
        api_key=api_key,
        collection_name="my_documents",
    )
    return qdrant