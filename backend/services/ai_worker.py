"""
services/ai_worker.py
The background worker function. This runs AFTER the API has already
responded 202 to the client - it is dispatched via FastAPI's
BackgroundTasks in routers/tasks.py.

Responsibilities:
  1. Mark the task PROCESSING.
  2. Route to the correct AI service based on task_type.
  3. Persist a Result row.
  4. Mark the task COMPLETED (or FAILED on any exception).

We open a fresh DB session here rather than reusing the request-scoped one,
because by the time this function runs, the original request's session has
already been closed.
"""
import logging
from uuid import UUID

from sqlmodel import Session, select

from database import engine
from models.task import Task, TaskStatus, TaskType
from models.image import Image
from models.result import Result
from services import vlm, diffusion, storage

logger = logging.getLogger("ai_worker")


async def process_ai_task(task_id: UUID) -> None:
    with Session(engine) as db:
        task = db.get(Task, task_id)
        if task is None:
            logger.error("Task %s not found when worker started", task_id)
            return

        try:
            task.status = TaskStatus.PROCESSING
            db.add(task)
            db.commit()

            result_text = None
            result_image_url = None

            if task.task_type in (TaskType.CAPTIONING, TaskType.VQA, TaskType.OCR):
                image = db.get(Image, task.image_id) if task.image_id else None
                if image is None:
                    raise ValueError("Source image not found for analysis task.")

                if task.task_type == TaskType.CAPTIONING:
                    result_text = await vlm.generate_caption(image.storage_url)
                elif task.task_type == TaskType.VQA:
                    if not task.prompt:
                        raise ValueError("VQA tasks require a prompt/question.")
                    result_text = await vlm.answer_visual_question(image.storage_url, task.prompt)
                elif task.task_type == TaskType.OCR:
                    result_text = await vlm.extract_text_ocr(image.storage_url)

            elif task.task_type == TaskType.TEXT_TO_IMAGE:
                if not task.prompt:
                    raise ValueError("Text-to-image tasks require a prompt.")
                image_bytes = await diffusion.generate_text_to_image(task.prompt)
                result_image_url = await storage.upload_image_to_storage(
                    image_bytes, "image/png", "png"
                )

            elif task.task_type == TaskType.IMAGE_VARIATION:
                image = db.get(Image, task.image_id) if task.image_id else None
                if image is None:
                    raise ValueError("Source image not found for variation task.")

                # Fetch the original bytes back from our own storage so we can
                # send them to the provider.
                import httpx
                async with httpx.AsyncClient(timeout=60.0) as http_client:
                    source_response = await http_client.get(image.storage_url)
                    source_response.raise_for_status()
                    source_bytes = source_response.content

                generated_bytes = await diffusion.generate_image_variation(
                    source_bytes, task.prompt or ""
                )
                result_image_url = await storage.upload_image_to_storage(
                    generated_bytes, "image/png", "png"
                )
            else:
                raise ValueError(f"Unknown task_type: {task.task_type}")

            result = Result(
                task_id=task.id,
                result_text=result_text,
                result_image_url=result_image_url,
            )
            db.add(result)

            task.status = TaskStatus.COMPLETED
            db.add(task)
            db.commit()

        except Exception as exc:  # noqa: BLE001 - we intentionally catch everything here
            # Never let a raw exception (which may contain sensitive details,
            # e.g. provider error bodies) leak to the client. Log it server-side
            # only, and store a sanitized message on the task.
            logger.exception("AI task %s failed", task_id)

            db.rollback()
            task = db.get(Task, task_id)
            if task is not None:
                task.status = TaskStatus.FAILED
                task.error_message = _sanitize_error_message(exc)
                db.add(task)
                db.commit()


def _sanitize_error_message(exc: Exception) -> str:
    """Returns a short, user-safe error message - never leaks API keys or
    full provider response bodies to the client."""
    from services.diffusion import ContentPolicyError

    if isinstance(exc, ContentPolicyError):
        return str(exc)
    return "The AI provider could not complete this request. Please try again."
