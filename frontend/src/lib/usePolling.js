"use client";

/**
 * lib/usePolling.js
 * Encapsulates the polling pattern required by the async task architecture:
 *   - call `run(taskId)` after a task is dispatched
 *   - every 2s, GET /api/tasks/{id} until status is COMPLETED or FAILED
 *   - exposes { status, result, error, isLoading } to the component
 *
 * Centralizing this in a hook keeps every feature panel (caption, VQA, OCR,
 * generation) from re-implementing its own setInterval/clearInterval logic.
 */
import { useCallback, useRef, useState } from "react";
import { getTaskStatus } from "./api";

const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 60; // 60 * 2s = 2 minutes safety ceiling

export function usePolling() {
  const [status, setStatus] = useState(null); // null | PENDING | PROCESSING | COMPLETED | FAILED
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);
  const attemptsRef = useRef(0);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const run = useCallback(
    (taskId) => {
      stop(); // clear any previous polling loop first
      setStatus("PENDING");
      setResult(null);
      setError(null);
      attemptsRef.current = 0;

      intervalRef.current = setInterval(async () => {
        attemptsRef.current += 1;

        if (attemptsRef.current > MAX_POLL_ATTEMPTS) {
          stop();
          setStatus("FAILED");
          setError("Timed out waiting for the task to complete.");
          return;
        }

        try {
          const data = await getTaskStatus(taskId);

          if (data.status === "COMPLETED") {
            stop();
            setStatus("COMPLETED");
            setResult(data.result);
          } else if (data.status === "FAILED") {
            stop();
            setStatus("FAILED");
            setError(data.error || "The task failed.");
          } else {
            // PENDING or PROCESSING - keep polling, no UI change needed
            setStatus(data.status);
          }
        } catch (err) {
          stop();
          setStatus("FAILED");
          setError(err.message || "Lost connection while polling for results.");
        }
      }, POLL_INTERVAL_MS);
    },
    [stop]
  );

  const isLoading = status === "PENDING" || status === "PROCESSING";

  return { status, result, error, isLoading, run, stop };
}
