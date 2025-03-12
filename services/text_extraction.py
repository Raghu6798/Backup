from pathlib import Path
import os 
from dotenv import load_dotenv
from mistralai import DocumentURLChunk, Mistral
import json

load_dotenv()
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def process_pdf(file_path: Path):
    file_path = Path(file_path)
    uploaded_file = client.files.upload(
        file={"file_name": file_path.stem, "content": file_path.read_bytes()},
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
    pdf_response = client.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url), 
        model="mistral-ocr-latest",
        include_image_base64=True
    )

    response_dict = json.loads(pdf_response.json())
    chunks = "\n".join(page["markdown"] for page in response_dict.get("pages", []))
    return chunks