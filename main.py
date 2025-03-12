from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes import pdf_route, query_route,chat_route

app = FastAPI(title="AI-Powered RAG System")

# ✅ Configure CORS
print("Configuring CORS...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5555",
        "http://localhost:5000"
    ],
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    expose_headers=["Content-Type", "Authorization"]
)

# ✅ Include routes
app.include_router(pdf_route.router, prefix="/pdf", tags=["PDF Processing"])
app.include_router(query_route.router, prefix="/api", tags=["Query Processing"])
app.include_router(chat_route.router,prefix="/chat",tags=["ChatBot"])

@app.get("/")
async def root():
    return {"message": "Welcome to the AI-Powered RAG System!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
