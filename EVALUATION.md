# Evaluation

This document demonstrates the platform's working features with screenshots
and the exact prompts used to produce them.

> **Note for evaluators**: screenshots below were captured running the app
> locally per the README setup steps, with real Anthropic and Stability AI
> API keys configured.

---

## 1. Image Captioning

**Prompt/instruction used:** (none required — captioning runs automatically
on the uploaded image)

**Source image:**

`![source image](./screenshots/caption-source.png)`

**Result:**

`![captioning result](./screenshots/caption-result.png)`

---

## 2. Visual Question Answering (VQA)

**Question asked:** `"What color is the main object in this image?"`

**Source image:**

`![source image](./screenshots/vqa-source.png)`

**Result:**

`![vqa result](./screenshots/vqa-result.png)`

---

## 3. Optical Character Recognition (OCR)

**Source image (containing visible text):**

`![source image](./screenshots/ocr-source.png)`

**Result:**

`![ocr result](./screenshots/ocr-result.png)`

---

## 4. Text-to-Image Generation

**Prompt used:** `"A lighthouse on a rocky cliff at sunset, watercolor painting style"`

**Result:**
![alt text](image.png)
`![text-to-image result](./screenshots/t2i-result.png)`

---

## 5. Image Variation

**Source image:**

`![source image](./screenshots/variation-source.png)`

**Style prompt used:** `"Make it look like an oil painting"`

**Result:**

`![variation result](./screenshots/variation-result.png)`

---

## 6. Async Polling — Network Tab Evidence

Screenshot of the browser DevTools Network tab during a task, showing the
initial `POST /api/tasks/analyze/caption` returning `202 Accepted`, followed
by repeated `GET /api/tasks/{task_id}` polling requests every ~2 seconds
until the final request returns `COMPLETED`.

`![network tab polling](./screenshots/network-polling.png)`

---

## 7. Database Verification

Screenshot from DBeaver/TablePlus (or `psql`) showing populated rows across
the `images`, `tasks`, and `results` tables with intact foreign key
relationships.

`![database tables](./screenshots/db-tables.png)`

---

## 8. Error Handling

Screenshot showing a `FAILED` task state in the UI (e.g. triggered by an
invalid/expired API key, a content-policy-rejected prompt, or a deliberately
broken `STORAGE_ENDPOINT_URL`), with the user-friendly error message
displayed rather than a raw 500.

`![error state](./screenshots/error-state.png)`
