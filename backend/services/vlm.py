"""
services/vlm.py
Vision-Language Model integration using Google's Gemini API (free tier).
Implements the three required analysis features:
  1. Image Captioning
  2. Visual Question Answering (VQA)
  3. Optical Character Recognition (OCR)
"""
import os
import httpx
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VLM_MODEL = os.getenv("VLM_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=GEMINI_API_KEY)

HTTP_TIMEOUT_SECONDS = 60.0


async def _fetch_image_bytes(image_url: str) -> tuple[bytes, str]:
    """Downloads the image and returns (raw_bytes, mime_type)."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as http_client:
        response = await http_client.get(image_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png")
        if content_type not in ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"):
            content_type = "image/png"
        return response.content, content_type


async def _call_gemini_vision(image_url: str, system_prompt: str, user_prompt: str) -> str:
    image_bytes, mime_type = await _fetch_image_bytes(image_url)

    response = await client.aio.models.generate_content(
        model=VLM_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            user_prompt,
        ],
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1024,
        ),
    )
    return (response.text or "").strip()


async def generate_caption(image_url: str) -> str:
    system_prompt = (
        "You are an image captioning assistant. Describe the contents of the "
        "image in a concise, accurate paragraph. Do not include introductory "
        "filler like 'This image shows'."
    )
    return await _call_gemini_vision(image_url, system_prompt, "Describe this image.")


async def answer_visual_question(image_url: str, question: str) -> str:
    system_prompt = (
        "You answer questions about images strictly based on what is visibly "
        "present. If the image does not contain the answer, say "
        "'I cannot determine this from the image.'"
    )
    user_prompt = f"Question: {question}"
    return await _call_gemini_vision(image_url, system_prompt, user_prompt)


async def extract_text_ocr(image_url: str) -> str:
    system_prompt = (
        "You perform OCR. Extract all readable text from the image. Maintain "
        "the original line breaks and formatting as closely as possible. If "
        "there is no text, return exactly 'NO_TEXT_FOUND'. Do not describe the "
        "image, only output the extracted text."
    )
    return await _call_gemini_vision(image_url, system_prompt, "Extract the text from this image.")