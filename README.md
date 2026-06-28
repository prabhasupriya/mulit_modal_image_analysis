# Multi-Modal Image Analysis and Generation Platform

A full-stack application that lets users upload images for AI-powered analysis
(captioning, visual question answering, OCR) and generate new images from text
prompts (text-to-image, image variation). Built with **Next.js** (frontend),
**FastAPI** (backend), **PostgreSQL** (database), and **S3-compatible object
storage** (local MinIO by default — no cloud account or card needed; AWS S3
or Cloudflare R2 also supported).

## Architecture

```
Next.js Frontend  <-- poll/HTTP -->  FastAPI Backend  <-->  PostgreSQL
                                           |
                                           +--> Object Storage (MinIO / S3 / R2)
                                           +--> Google Gemini (VLM)
                                           +--> Stability AI (Diffusion)
```

All AI calls run asynchronously: the backend returns a `task_id` immediately
(HTTP 202), processes the AI request in a background task, and the frontend
polls `GET /api/tasks/{task_id}` every 2 seconds until the result is ready.

**Analysis features (VLM via Google Gemini):**
1. Image Captioning
2. Visual Question Answering (VQA)
3. Optical Character Recognition (OCR)

**Generation features (Diffusion via Stability AI):**
1. Text-to-Image Generation
2. Image Variation (image-to-image remix)

## Prerequisites

- Docker + Docker Compose
- Node.js 18+ and npm
- Python 3.11+
- A free [Google Gemini API key](https://aistudio.google.com/apikey) — no
  credit card required, generated instantly through Google AI Studio
- A [Stability AI API key](https://platform.stability.ai/)
- Object storage — **no signup needed**: `docker-compose.yml` includes a
  local [MinIO](https://min.io/) container, which is fully S3-compatible and
  free with zero external account required. (AWS S3 or Cloudflare R2 work
  too, if you'd rather use a cloud bucket — see "Using a cloud bucket
  instead" below.)

## Setup

### 1. Clone and configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `GEMINI_API_KEY` — free, from Google AI Studio (see Prerequisites above)
- `STABILITY_API_KEY` — from the Stability AI platform
- `STORAGE_*` — the defaults in `.env.example` already point at the local
  MinIO container started by `docker-compose.yml` (user/pass `minioadmin` /
  `minioadmin`, endpoint `http://localhost:9000`). You don't need to change
  these unless you want to use a cloud bucket instead — see below.

#### Getting a free Gemini API key

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with any Google account
3. Click **Create API key** (no payment method, no project setup required
   for the free tier)
4. Copy the key (starts with `AIza...`) into `GEMINI_API_KEY` in `.env`

The free tier covers a generous number of requests per day at no cost,
which is more than enough to run and test every analysis feature in this
project.

#### Using a cloud bucket instead (optional)

If you'd rather use Cloudflare R2 or AWS S3 instead of local MinIO, comment
out the MinIO block in `.env` and uncomment the matching block for R2 or S3
(also provided in `.env.example`):
  - **R2**: set `STORAGE_REGION=auto`, `STORAGE_ENDPOINT_URL` to your
    account's R2 endpoint, and `STORAGE_PUBLIC_BASE_URL` to your bucket's
    public R2.dev URL (enable this under bucket → Settings → Public Access).
    Requires a Cloudflare account with R2 enabled (free tier, but does
    require adding a card to activate the subscription).
  - **AWS S3**: leave `STORAGE_ENDPOINT_URL` blank, set `STORAGE_REGION` to
    your bucket's region, and give the bucket a public-read policy (or use
    `generate_presigned_get_url` in `services/storage.py` to keep it
    private). Also set `STORAGE_AUTO_PROVISION_BUCKET=false` for both R2 and
    S3, since that flag is only meant for local MinIO.

### 2. Start the infrastructure (database + object storage)

```bash
docker-compose up -d
```

This starts two containers:
- **PostgreSQL 15** on port 5432, with the credentials from `docker-compose.yml`
  (matching `DATABASE_URL` in `.env.example`)
- **MinIO** on ports 9000 (S3 API) and 9001 (web console), with credentials
  `minioadmin` / `minioadmin` (matching the `STORAGE_*` defaults in
  `.env.example`)

Verify both are healthy:

```bash
docker-compose ps
```

You can optionally browse your bucket visually at `http://localhost:9001`
(log in with `minioadmin` / `minioadmin`) once the backend has started and
created the bucket automatically — see step 3.

### 3. Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend creates its database tables automatically on startup, and (when
`STORAGE_AUTO_PROVISION_BUCKET=true`, the default for MinIO) also creates
the storage bucket and sets it to public-read if it doesn't already exist —
no separate migration or bucket-setup step needed for this project. Visit
`http://localhost:8000/docs` to see the interactive API docs and confirm
it's running.

### 4. Start the frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`.

By default the frontend talks to `http://localhost:8000`. To override, create
`frontend/.env.local` with:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Using the app

1. **Analysis Dashboard** — upload a JPEG/PNG (max 5MB), then click "Run" on
   Captioning, VQA (enter a question first), or OCR. Each shows a status LED
   (queued → processing → completed) while polling in the background.
2. **Generation Studio** — for Text-to-Image, enter a prompt and click
   Generate. For Image Variation, upload a source image, optionally describe
   a style direction, and click Generate Variation.

## Project structure

```
project-root/
├── backend/
│   ├── main.py              # FastAPI app entry point + CORS + DB init
│   ├── database.py          # SQLModel engine/session setup
│   ├── requirements.txt
│   ├── models/               # Image, Task, Result tables
│   ├── routers/               # images.py (upload), tasks.py (async + polling)
│   ├── services/
│   │   ├── storage.py        # S3/R2 client
│   │   ├── vlm.py            # Google Gemini vision integration
│   │   ├── diffusion.py      # Stability AI integration
│   │   └── ai_worker.py      # Background task router/orchestrator
│   └── Dockerfile
├── frontend/
│   ├── src/app/               # Next.js App Router pages + layout + styles
│   ├── src/components/        # ImageUploader, AnalysisDashboard, GenerationStudio, etc.
│   └── src/lib/                # api.js (HTTP client), usePolling.js (polling hook)
├── docker-compose.yml
├── .env.example
└── EVALUATION.md
```

## Database schema

- **images**: `id, filename, storage_url, content_type, created_at`
- **tasks**: `id, task_type, status, image_id (FK -> images), prompt, error_message, created_at, updated_at`
- **results**: `id, task_id (FK -> tasks), result_text, result_image_url, created_at`

## Error handling notes

- Uploads are validated for content type (`image/jpeg`, `image/png`) and size
  (5MB max) on both frontend and backend.
- The background worker catches all exceptions from AI provider calls,
  marks the task `FAILED`, and stores a sanitized error message — raw
  provider error bodies (which can include sensitive details) are logged
  server-side only, never returned to the client.
- Stability AI content-policy rejections (HTTP 403) are caught specifically
  and surfaced as a friendly message rather than a generic 500.
- All outbound HTTP calls (to Gemini, Stability, and object storage) have
  explicit timeouts so a hung provider can never leave a task stuck in
  `PROCESSING` forever or block the server's event loop.

## Troubleshooting

- **CORS errors**: confirm `FRONTEND_ORIGIN` in `.env` matches exactly where
  your frontend runs (`http://localhost:3000` by default).
- **Database connection refused**: make sure `docker-compose up -d` succeeded
  and `DATABASE_URL` in `.env` matches the credentials in `docker-compose.yml`.
- **Upload fails with a storage/connection error**: confirm the MinIO
  container is running (`docker-compose ps`) and reachable at
  `http://localhost:9000`. You can sanity-check it directly by visiting
  `http://localhost:9001` (the MinIO web console) and logging in with
  `minioadmin` / `minioadmin`.
- **Generated image URLs don't load in the browser**: for MinIO, confirm
  `STORAGE_AUTO_PROVISION_BUCKET=true` so the bucket gets the public-read
  policy automatically — check the backend startup logs for a line like
  `Public-read policy applied to bucket '...'`. For R2/S3, this usually means
  your bucket isn't public, or `STORAGE_PUBLIC_BASE_URL` isn't set correctly.
- **Tasks stuck in PENDING**: check the backend terminal output — exceptions
  in the background worker are logged there even though the client only sees
  a sanitized message.

  ## youtude video -[watch here](https://youtu.be/mIRTfJCvDZI)