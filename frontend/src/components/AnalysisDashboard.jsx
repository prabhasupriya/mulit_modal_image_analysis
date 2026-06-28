"use client";

/**
 * components/AnalysisDashboard.jsx
 * Lets the user upload an image, then run any of the three VLM-backed
 * analysis features against it: Captioning, VQA, OCR.
 * Each feature has its own polling state so running one doesn't clobber
 * another's in-flight result.
 */
import { useState } from "react";
import ImageUploader from "./ImageUploader";
import TaskStatusIndicator from "./TaskStatusIndicator";
import { usePolling } from "../lib/usePolling";
import { startAnalysisTask } from "../lib/api";

function AnalysisFeaturePanel({ title, analysisType, image, requiresPrompt }) {
  const { status, result, error, isLoading, run } = usePolling();
  const [question, setQuestion] = useState("");
  const [dispatchError, setDispatchError] = useState(null);

  const handleRun = async () => {
    if (!image) return;
    setDispatchError(null);

    if (requiresPrompt && !question.trim()) {
      setDispatchError("Please enter a question first.");
      return;
    }

    try {
      const { task_id } = await startAnalysisTask(
        analysisType,
        image.id,
        requiresPrompt ? question.trim() : undefined
      );
      run(task_id);
    } catch (err) {
      setDispatchError(err.message || "Could not start the task.");
    }
  };

  return (
    <div className="panel" style={{ marginBottom: 16 }}>
      <h2>{title}</h2>

      {requiresPrompt && (
        <div className="field">
          <label htmlFor={`${analysisType}-question`}>Question</label>
          <input
            id={`${analysisType}-question`}
            type="text"
            placeholder="What is happening in this image?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </div>
      )}

      <div className="action-row">
        <button
          className="btn btn-primary"
          onClick={handleRun}
          disabled={!image || isLoading}
        >
          {isLoading ? "Running…" : "Run"}
        </button>
      </div>

      <TaskStatusIndicator status={status} />

      {dispatchError && <div className="error-box">{dispatchError}</div>}
      {error && <div className="error-box">{error}</div>}

      {result?.result_text && <div className="result-box">{result.result_text}</div>}
    </div>
  );
}

export default function AnalysisDashboard() {
  const [uploadedImage, setUploadedImage] = useState(null);

  return (
    <div className="panel-grid">
      <div className="panel">
        <h2>Source Image</h2>
        <ImageUploader onUploaded={setUploadedImage} uploadedImage={uploadedImage} />
        {!uploadedImage && (
          <p className="empty-hint" style={{ marginTop: 12 }}>
            Upload an image to enable the analysis tools.
          </p>
        )}
      </div>

      <div>
        <AnalysisFeaturePanel
          title="01 — Image Captioning"
          analysisType="caption"
          image={uploadedImage}
          requiresPrompt={false}
        />
        <AnalysisFeaturePanel
          title="02 — Visual Question Answering"
          analysisType="vqa"
          image={uploadedImage}
          requiresPrompt={true}
        />
        <AnalysisFeaturePanel
          title="03 — Optical Character Recognition"
          analysisType="ocr"
          image={uploadedImage}
          requiresPrompt={false}
        />
      </div>
    </div>
  );
}
