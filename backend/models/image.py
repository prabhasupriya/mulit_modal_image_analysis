"""
models/image.py
Represents an uploaded source image and where it lives in object storage.
"""
import uuid
from datetime import datetime
from sqlmodel import SQLModel, Field


class Image(SQLModel, table=True):
    __tablename__ = "images"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    filename: str
    storage_url: str
    content_type: str = Field(default="image/png")
    created_at: datetime = Field(default_factory=datetime.utcnow)
