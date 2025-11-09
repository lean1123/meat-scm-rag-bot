from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat
from app.routes import conversation
from app.routes import message_route

from app.configurations.weaviate_config import init_weaviate_client, close_weaviate_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize resources on startup
    init_weaviate_client()
    try:
        yield
    finally:
        # Close/cleanup resources on shutdown
        close_weaviate_client()

app = FastAPI(
    title="Farm AI Chatbot API",
    description="API cho chatbot quản lý đàn vật nuôi thông minh.",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(message_route.router, prefix="/api", tags=["Messages"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Farm AI Chatbot API!"}
