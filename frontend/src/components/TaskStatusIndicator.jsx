"use client";

/**
 * components/TaskStatusIndicator.jsx
 * Small reusable "LED + label" readout for the current task status.
 * Used by every feature panel so the polling state always looks consistent.
 */
export default function TaskStatusIndicator({ status }) {
  if (!status) return null;

  const ledClass = status.toLowerCase();
  const label =
    status === "PENDING"
      ? "Queued"
      : status === "PROCESSING"
      ? "Processing"
      : status === "COMPLETED"
      ? "Completed"
      : status === "FAILED"
      ? "Failed"
      : status;

  return (
    <div className="status-line">
      <span className={`led ${ledClass}`} />
      <span>{label}</span>
    </div>
  );
}
