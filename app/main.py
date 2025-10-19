from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat
from app.routes import conversation
from app.routes import message

app = FastAPI(
    title="Farm AI Chatbot API",
    description="API cho chatbot quản lý đàn vật nuôi thông minh.",
    version="1.0.0"
)

# Cấu hình CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(conversation.router, prefix="/api", tags=["Conversations"])
app.include_router(message.router, prefix="/api", tags=["Messages"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Farm AI Chatbot API!"}
