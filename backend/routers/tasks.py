"""
routers/tasks.py
The core asynchronous pattern of the whole application:

  1. POST /api/tasks/analyze/{analysis_type}  -> creates a Task, dispatches
     the background worker, returns 202 + task_id immediately.
  2. POST /api/tasks/generate/{generation_type} -> same pattern for
     generation tasks (no source image required for text-to-image).
  3. GET  /api/tasks/{task_id} -> polling endpoint. Returns current status,
     and the Result payload once COMPLETED.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_db
from models.task import Task, TaskStatus, TaskType
from models.image import Image
from models.result import Result
from services.ai_worker import process_ai_task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

ANALYSIS_TYPES = {"caption": TaskType.CAPTIONING, "vqa": TaskType.VQA, "ocr": TaskType.OCR}
GENERATION_TYPES = {
    "text-to-image": TaskType.TEXT_TO_IMAGE,
    "variation": TaskType.IMAGE_VARIATION,
}


class AnalysisRequest(BaseModel):
    image_id: str
    prompt: Optional[str] = None  # required for VQA, ignored otherwise


class GenerationRequest(BaseModel):
    prompt: str
    image_id: Optional[str] = None  # required for variation, ignored for text-to-image


@router.post("/analyze/{analysis_type}", status_code=202)
async def start_analysis(
    analysis_type: str,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    task_type = ANALYSIS_TYPES.get(analysis_type)
    if task_type is None:
        raise HTTPException(status_code=400, detail=f"Unknown analysis_type '{analysis_type}'.")

    image = db.get(Image, request.image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found.")

    if task_type == TaskType.VQA and not request.prompt:
        raise HTTPException(status_code=400, detail="VQA requires a 'prompt' (the question).")

    task = Task(
        task_type=task_type,
        status=TaskStatus.PENDING,
        image_id=image.id,
        prompt=request.prompt,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(process_ai_task, task.id)

    return {"task_id": str(task.id), "status": task.status}


@router.post("/generate/{generation_type}", status_code=202)
async def start_generation(
    generation_type: str,
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    task_type = GENERATION_TYPES.get(generation_type)
    if task_type is None:
        raise HTTPException(status_code=400, detail=f"Unknown generation_type '{generation_type}'.")

    if not request.prompt:
        raise HTTPException(status_code=400, detail="Generation requires a 'prompt'.")

    image_id = None
    if task_type == TaskType.IMAGE_VARIATION:
        if not request.image_id:
            raise HTTPException(status_code=400, detail="Image variation requires an 'image_id'.")
        image = db.get(Image, request.image_id)
        if image is None:
            raise HTTPException(status_code=404, detail="Source image not found.")
        image_id = image.id

    task = Task(
        task_type=task_type,
        status=TaskStatus.PENDING,
        image_id=image_id,
        prompt=request.prompt,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(process_ai_task, task.id)

    return {"task_id": str(task.id), "status": task.status}


@router.get("/{task_id}")
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    response = {
        "task_id": str(task.id),
        "task_type": task.task_type,
        "status": task.status,
    }

    if task.status == TaskStatus.COMPLETED:
        result = db.exec(select(Result).where(Result.task_id == task.id)).first()
        if result:
            response["result"] = {
                "result_text": result.result_text,
                "result_image_url": result.result_image_url,
            }

    if task.status == TaskStatus.FAILED:
        response["error"] = task.error_message

    return response
