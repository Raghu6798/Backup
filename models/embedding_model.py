from langchain_huggingface import HuggingFaceEmbeddings

def get_embedding_model():
    model_name = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
