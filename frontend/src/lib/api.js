/**
 * lib/api.js
 * Thin client for talking to the FastAPI backend. Centralizing this here
 * means components never construct fetch() calls or URLs by hand.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function parseJsonOrThrow(response) {
  let body = null;
  try {
    body = await response.json();
  } catch {
    // no JSON body - fall through to generic error below
  }
  if (!response.ok) {
    const message = body?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return body;
}

export async function uploadImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/images/upload`, {
    method: "POST",
    body: formData,
  });
  return parseJsonOrThrow(response);
}

export async function startAnalysisTask(analysisType, imageId, prompt) {
  const response = await fetch(`${API_BASE_URL}/api/tasks/analyze/${analysisType}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id: imageId, prompt: prompt || null }),
  });
  return parseJsonOrThrow(response);
}

export async function startGenerationTask(generationType, prompt, imageId) {
  const response = await fetch(`${API_BASE_URL}/api/tasks/generate/${generationType}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, image_id: imageId || null }),
  });
  return parseJsonOrThrow(response);
}

export async function getTaskStatus(taskId) {
  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`);
  return parseJsonOrThrow(response);
}

export { API_BASE_URL };
