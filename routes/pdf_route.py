from fastapi import APIRouter, UploadFile, File
from services.text_extraction import process_pdf
from sample.chunking import chunk_text
from database.qdrant_store import get_qdrant_store
from loguru import logger

router = APIRouter()

# Configure Loguru
logger.add("logs/pdf_processing.log", rotation="10MB", level="INFO")

@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Handles PDF upload, extracts text, chunks it, embeds it, and stores it in Qdrant.
    """
    logger.info(f"Received file: {file.filename}")

    # Save uploaded file temporarily
    file_path = f"/tmp/{file.filename}"
    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logger.info(f"File saved successfully at {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return {"error": "Failed to process file"}

    # Extract text
    try:
        extracted_text = process_pdf(file_path)
        logger.info(f"Extracted text from {file.filename}")
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return {"error": "Text extraction failed"}

    # Chunk text
    chunks = chunk_text(extracted_text)
    logger.info(f"Chunked the extracted text into {len(chunks)} segments")

    # Add chunks to Qdrant
    try:
        qdrant = get_qdrant_store()
        qdrant.add_documents(chunks)
        logger.info(f"Added {len(chunks)} chunks to Qdrant")
    except Exception as e:
        logger.error(f"Failed to add chunks to Qdrant: {e}")
        return {"error": "Failed to store chunks in Qdrant"}

    return {"message": "PDF processed and stored in Qdrant!", "chunks": len(chunks)}