"""
routers/images.py
Handles image upload: validates the file, stores it in object storage,
and creates an Image record.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel import Session

from database import get_db
from models.image import Image
from services.storage import upload_image_to_storage

router = APIRouter(prefix="/api/images", tags=["images"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB, matches the spec's frontend limit


@router.post("/upload", status_code=201)
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only JPEG and PNG images are allowed.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum allowed size is 5MB.",
        )
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    extension = "jpg" if file.content_type == "image/jpeg" else "png"
    storage_url = await upload_image_to_storage(file_bytes, file.content_type, extension)

    image = Image(
        filename=file.filename or f"upload.{extension}",
        storage_url=storage_url,
        content_type=file.content_type,
    )
    db.add(image)
    db.commit()
    db.refresh(image)

    return {"id": str(image.id), "url": image.storage_url, "filename": image.filename}


@router.get("/{image_id}")
async def get_image(image_id: str, db: Session = Depends(get_db)):
    image = db.get(Image, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found.")
    return {"id": str(image.id), "url": image.storage_url, "filename": image.filename}
