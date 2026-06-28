"""
main.py
FastAPI application entry point. Sets up CORS, initializes the database
on startup, and wires up the images/tasks routers.
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

from database import init_db
from routers import images, tasks
from services.storage import ensure_bucket_exists_and_public

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_bucket_exists_and_public()
    yield


app = FastAPI(title="Multi-Modal AI Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router)
app.include_router(tasks.router)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "multimodal-ai-platform-backend"}
