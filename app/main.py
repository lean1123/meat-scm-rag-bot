from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat
from app.routes import conversation
from app.routes import message

from app.configurations.weaviate_config import init_weaviate_client, close_weaviate_client

app = FastAPI(
    title="Farm AI Chatbot API",
    description="API cho chatbot quản lý đàn vật nuôi thông minh.",
    version="1.0.0"
)

# Cấu hình CORS
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost:8082",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers (removed the message router)
app.include_router(chat.router, prefix="/api")
app.include_router(conversation.router, prefix="/api", tags=["Conversations"])
app.include_router(message.router, prefix="/api", tags=["Messages"])


@app.on_event("startup")
async def on_startup():
    # Initialize Weaviate client for application lifetime
    init_weaviate_client()


@app.on_event("shutdown")
async def on_shutdown():
    # Close Weaviate client to avoid resource warnings
    close_weaviate_client()


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Farm AI Chatbot API!"}
