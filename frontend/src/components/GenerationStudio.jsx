"use client";

/**
 * components/GenerationStudio.jsx
 * Two generation features:
 *   - Text-to-Image: just needs a prompt.
 *   - Image Variation: needs a source image (uploaded here) + a prompt
 *     describing the desired stylistic direction.
 */
import { useState } from "react";
import ImageUploader from "./ImageUploader";
import TaskStatusIndicator from "./TaskStatusIndicator";
import { usePolling } from "../lib/usePolling";
import { startGenerationTask } from "../lib/api";

function TextToImagePanel() {
  const [prompt, setPrompt] = useState("");
  const [dispatchError, setDispatchError] = useState(null);
  const { status, result, error, isLoading, run } = usePolling();

  const handleGenerate = async () => {
    setDispatchError(null);
    if (!prompt.trim()) {
      setDispatchError("Please enter a prompt describing the image.");
      return;
    }
    try {
      const { task_id } = await startGenerationTask("text-to-image", prompt.trim());
      run(task_id);
    } catch (err) {
      setDispatchError(err.message || "Could not start generation.");
    }
  };

  return (
    <div className="panel" style={{ marginBottom: 16 }}>
      <h2>01 — Text-to-Image Generation</h2>
      <div className="field">
        <label htmlFor="t2i-prompt">Prompt</label>
        <textarea
          id="t2i-prompt"
          rows={3}
          placeholder="A lighthouse on a cliff at sunset, watercolor style"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </div>
      <div className="action-row">
        <button className="btn btn-primary" onClick={handleGenerate} disabled={isLoading}>
          {isLoading ? "Generating…" : "Generate"}
        </button>
      </div>
      <TaskStatusIndicator status={status} />
      {dispatchError && <div className="error-box">{dispatchError}</div>}
      {error && <div className="error-box">{error}</div>}
      {result?.result_image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={result.result_image_url} alt="Generated result" className="result-image" />
      )}
    </div>
  );
}

function ImageVariationPanel() {
  const [sourceImage, setSourceImage] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [dispatchError, setDispatchError] = useState(null);
  const { status, result, error, isLoading, run } = usePolling();

  const handleGenerate = async () => {
    setDispatchError(null);
    if (!sourceImage) {
      setDispatchError("Upload a source image first.");
      return;
    }
    try {
      const { task_id } = await startGenerationTask(
        "variation",
        prompt.trim() || "A creative stylistic variation of this image",
        sourceImage.id
      );
      run(task_id);
    } catch (err) {
      setDispatchError(err.message || "Could not start generation.");
    }
  };

  return (
    <div className="panel">
      <h2>02 — Image Variation</h2>
      <ImageUploader onUploaded={setSourceImage} uploadedImage={sourceImage} />

      <div className="field" style={{ marginTop: 14 }}>
        <label htmlFor="variation-prompt">Style direction (optional)</label>
        <input
          id="variation-prompt"
          type="text"
          placeholder="Make it look like an oil painting"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
      </div>

      <div className="action-row">
        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={!sourceImage || isLoading}
        >
          {isLoading ? "Generating…" : "Generate Variation"}
        </button>
      </div>

      <TaskStatusIndicator status={status} />
      {dispatchError && <div className="error-box">{dispatchError}</div>}
      {error && <div className="error-box">{error}</div>}
      {result?.result_image_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={result.result_image_url} alt="Generated variation" className="result-image" />
      )}
    </div>
  );
}

export default function GenerationStudio() {
  return (
    <div>
      <TextToImagePanel />
      <ImageVariationPanel />
    </div>
  );
}
