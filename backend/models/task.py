"""
models/task.py
Tracks the lifecycle of an asynchronous AI job (analysis or generation).
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field


class TaskType(str, Enum):
    CAPTIONING = "CAPTIONING"
    VQA = "VQA"
    OCR = "OCR"
    TEXT_TO_IMAGE = "TEXT_TO_IMAGE"
    IMAGE_VARIATION = "IMAGE_VARIATION"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_type: TaskType
    status: TaskStatus = Field(default=TaskStatus.PENDING)

    # Optional because text-to-image generation has no source image.
    image_id: Optional[uuid.UUID] = Field(default=None, foreign_key="images.id")

    prompt: Optional[str] = Field(default=None)
    error_message: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
