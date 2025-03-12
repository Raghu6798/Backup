from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text(text: str):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200,
        separators=["\n\n", "\n", ".", "!", "?", ",", " "]
    )
    return text_splitter.create_documents([text])
