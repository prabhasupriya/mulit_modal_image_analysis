"use client";

/**
 * components/ImageUploader.jsx
 * Handles file selection (click or drag-and-drop), client-side validation
 * (type + 5MB size limit matching the backend's enforcement), an instant
 * local preview via URL.createObjectURL, and the actual upload call.
 */
import { useCallback, useRef, useState } from "react";
import { uploadImage } from "../lib/api";

const ALLOWED_TYPES = ["image/jpeg", "image/png"];
const MAX_SIZE_BYTES = 5 * 1024 * 1024;

export default function ImageUploader({ onUploaded, uploadedImage }) {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback(
    async (file) => {
      if (!file) return;
      setError(null);

      if (!ALLOWED_TYPES.includes(file.type)) {
        setError("Only JPEG and PNG images are supported.");
        return;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError("File too large. Maximum size is 5MB.");
        return;
      }

      // Instant local preview, before the network request resolves.
      const localUrl = URL.createObjectURL(file);
      setPreviewUrl(localUrl);

      setIsUploading(true);
      try {
        const data = await uploadImage(file);
        onUploaded(data);
      } catch (err) {
        setError(err.message || "Upload failed. Please try again.");
      } finally {
        setIsUploading(false);
      }
    },
    [onUploaded]
  );

  const onInputChange = (e) => handleFile(e.target.files?.[0]);

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const displayImageUrl = uploadedImage?.url || previewUrl;

  return (
    <div>
      <div
        className={`dropzone ${isDragOver ? "dragover" : ""}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          onChange={onInputChange}
        />
        <p>
          {isUploading
            ? "Uploading…"
            : "Click or drag an image here (JPEG/PNG, max 5MB)"}
        </p>
      </div>

      {error && <div className="error-box">{error}</div>}

      {displayImageUrl && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={displayImageUrl} alt="Uploaded preview" className="preview-image" />
      )}
    </div>
  );
}
