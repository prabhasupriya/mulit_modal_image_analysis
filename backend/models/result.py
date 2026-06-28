"""
models/result.py
Stores the output of a completed task. Separated from Task because the
output shape differs wildly between text results (captions/OCR/VQA) and
binary/image results (generation outputs).
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Result(SQLModel, table=True):
    __tablename__ = "results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="tasks.id")

    result_text: Optional[str] = Field(default=None)
    result_image_url: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
