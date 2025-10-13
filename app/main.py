from fastapi import FastAPI
from app.routes import chat
from app.routes import auth

app = FastAPI(
    title="Farm AI Chatbot API",
    description="API cho chatbot quản lý đàn vật nuôi thông minh.",
    version="1.0.0"
)

app.include_router(auth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Farm AI Chatbot API!"}