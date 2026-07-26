# RAG Project using ColPali Method

A Retrieval-Augmented Generation (RAG) application that indexes and searches PDF documents using **ColPali** — a vision-language-model-based retrieval method that embeds document pages as images instead of relying on OCR and text chunking.

The project is a full-stack app: a **FastAPI backend** (PDF ingestion, ColPali embeddings, vector search) and a **React + Vite + TypeScript frontend** (upload UI, query interface, results view).

---

## ✨ Features

- 📄 **PDF ingestion** — upload a PDF, it's split into page images and embedded with ColPali (no OCR)
- 🔍 **Semantic search** — query in natural language and get back the most relevant page(s), scored by similarity
- 🧑‍🤝‍🧑 **Per-user sessions** — HMAC-signed anonymous user IDs (no login required) with per-user document isolation
- 📊 **Storage quotas** — configurable per-user quota (default 100 MB) and concurrent upload limits (default 3)
- ⏳ **Auto-expiring documents** — uploaded documents have a TTL (default 24h) and are cleaned up automatically
- 🧹 **Scheduled cleanup jobs** — background jobs purge expired documents from the vector DB and orphaned files from S3
- ☁️ **S3-backed page storage** — page images are stored in S3 and served via pre-signed URLs
- ⚡ **Serverless-ready backend** — deployable to AWS Lambda (via Mangum) using an included SAM template

---

## 🧠 What is ColPali?

[ColPali](https://github.com/illuin-tech/colpali) embeds entire document page **images** using a vision-language model, rather than extracting and chunking text first. This lets it handle tables, figures, and complex layouts that traditional OCR-based RAG pipelines often struggle with. This project uses the `vidore/colpali-v1.2` checkpoint via the `colpali-engine` library.

---

## 🏗️ Architecture

```
┌───────────────────────┐        REST API (/api/v1)       ┌──────────────────────────────┐
│   React + Vite         │ ─────────────────────────────▶ │   FastAPI Backend             │
│   Frontend (TS)        │ ◀───────────────────────────── │                                │
│                        │                                 │  ┌──────────────────────────┐  │
│  - Document upload     │                                 │  │ Document Ingestion        │  │
│  - Search / query      │                                 │  │  (PyMuPDF, pdf2image)     │  │
│  - Results viewer      │                                 │  └──────────────────────────┘  │
└───────────────────────┘                                 │  ┌──────────────────────────┐  │
                                                            │  │ ColPali Embeddings        │  │
                                                            │  │  (colpali-engine, torch)  │  │
                                                            │  └──────────────────────────┘  │
                                                            └──────────────┬────────────────┘
                                                                           │
                                              ┌────────────────────────────┼────────────────────────────┐
                                              ▼                                                          ▼
                                   ┌─────────────────────┐                                   ┌───────────────────────┐
                                   │   Qdrant Vector DB    │                                   │   AWS S3 (page images) │
                                   │  (multi-vector search)│                                   │  (pre-signed URLs)     │
                                   └─────────────────────┘                                   └───────────────────────┘

                 Scheduled jobs (EventBridge / cron): expire old documents from Qdrant + S3 every few hours
```

---

## 📁 Project Structure

```
rag-project-using-copali-method/
├── backend/
│   ├── main.py                          # FastAPI app entrypoint
│   ├── lambda_handler.py                # AWS Lambda entrypoint (Mangum)
│   ├── template.yaml                    # AWS SAM template (Lambda + EventBridge cron jobs)
│   ├── requirements.txt
│   └── app/
│       ├── api/
│       │   ├── dependencies.py          # Qdrant + auth dependencies
│       │   └── routes/
│       │       ├── auth.py              # Anonymous user ID issuance/verification
│       │       ├── ingest.py            # PDF upload + quota endpoint
│       │       ├── search.py            # Semantic search endpoint
│       │       ├── sessions.py          # Session info endpoint
│       │       └── fetch_image.py       # Pre-signed S3 image URLs
│       ├── config/
│       │   ├── settings.py              # Env-driven configuration
│       │   └── .env.example
│       ├── core/
│       │   ├── auth.py                  # HMAC user ID signing/verification
│       │   ├── middleware.py            # X-User-ID verification middleware
│       │   ├── quota_manager.py         # Per-user storage & upload quotas
│       │   └── embeddings/
│       │       └── embeddings_model.py  # ColPali embedding model wrapper
│       ├── db/
│       │   └── qdrant_vectorstore.py    # Qdrant collection setup & search
│       ├── processor/
│       │   └── document_ingestion.py    # PDF → page images → S3
│       ├── storage/
│       │   └── s3_storage.py            # S3 upload / pre-signed URLs
│       └── scheduler/
│           ├── scheduler.py             # Cleanup job logic
│           └── lambda_handlers.py       # Lambda handlers for scheduled cleanup
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── main.tsx
    │   ├── pages/Home.tsx
    │   ├── components/
    │   │   ├── DocumentUpload.tsx
    │   │   ├── QueryInput.tsx
    │   │   ├── ResultsList.tsx
    │   │   ├── ResultCard.tsx
    │   │   └── ClearSession.tsx
    │   ├── api/
    │   │   ├── client.ts                # Axios API client
    │   │   └── userIdManager.ts         # Stores/retrieves the signed user ID
    │   └── types/index.ts
    ├── package.json
    └── vite.config.ts
```

---

## 🛠️ Tech Stack

| Layer            | Technology |
|-------------------|------------|
| Retrieval          | [ColPali](https://github.com/illuin-tech/colpali) (`colpali-engine`, `vidore/colpali-v1.2`) via PyTorch |
| Vector DB          | [Qdrant](https://qdrant.tech/) (multi-vector search) |
| Backend framework  | FastAPI + Uvicorn |
| PDF processing     | PyMuPDF (`fitz`), `pdf2image`, Pillow |
| Object storage     | AWS S3 (page images, via `boto3`) |
| Serverless deploy  | AWS Lambda + Mangum + AWS SAM |
| Scheduled jobs     | AWS EventBridge Scheduler (cron cleanup) |
| Frontend framework | React 19 + TypeScript + Vite |
| Styling            | Tailwind CSS v4 |
| HTTP client        | Axios |
| Icons              | lucide-react |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11
- Node.js 18+ and npm
- A running [Qdrant](https://qdrant.tech/) instance (local via Docker, or Qdrant Cloud)
- An AWS S3 bucket + AWS credentials (page images are stored in S3 — this is required, not optional)
- (Recommended) a GPU for faster ColPali embedding generation — CPU works but is slower

### 1. Clone the repository

```bash
git clone https://github.com/priyanks25coder/rag-project-using-copali-method.git
cd rag-project-using-copali-method
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example env file and fill in your own values:

```bash
cp app/config/.env.example app/config/.env
```

Key variables in `app/config/.env`:

```
ENVIRONMENT=development
QDRANT_URL=http://localhost:6333          # or your Qdrant Cloud URL
QDRANT_API_KEY=                            # required in production
QDRANT_COLLECTION_NAME=rag-docs
COLPALI_MODEL_NAME=vidore/colpali-v1.2
EMBEDDING_DIM=128
MAX_PDF_SIZE_MB=10
MAX_PDF_PAGES=20
USER_QUOTA_MB=100
USER_CONCURRENT_UPLOADS=3
DOCUMENT_TTL_SECONDS=86400
USER_ID_SECRET=<a strong random string>
S3_BUCKET_NAME=<your-s3-bucket-name>
AWS_REGION=us-east-1
FRONTEND_URL=http://localhost:5173
```

Run a local Qdrant instance if you don't already have one:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

The API docs will be available at `http://localhost:8000/docs`.

### 3. Frontend setup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects `VITE_API_BASE_URL` to point at the backend (already set to `http://localhost:8000` in `.env.development`). It will start on Vite's dev server, typically `http://localhost:5173`.

---

## 🧪 Usage

1. Start Qdrant, the backend, and the frontend as described above.
2. Open the frontend in your browser — an anonymous, HMAC-signed user ID is generated and stored automatically.
3. Upload a PDF (max size and page count are configurable, defaults: 10 MB / 20 pages).
4. Enter a natural-language query — the backend embeds it with ColPali and returns the most relevant page(s) from *your* uploaded documents, ranked by similarity score.
5. Uploaded documents expire automatically after the configured TTL (default 24 hours); scheduled jobs clean up expired data from Qdrant and S3.

---

## 📡 API Overview

All routes are prefixed with `/api/v1` and (aside from `/auth`) require an `X-User-ID` header.

| Method | Endpoint | Description |
|--------|----------|--------------|
| POST | `/auth/generate-user-id` | Issue a new signed anonymous user ID |
| POST | `/auth/verify-user-id` | Verify a user ID token |
| POST | `/ingest/` | Upload and index a PDF |
| GET | `/ingest/quota` | Get the current user's storage/upload quota |
| POST | `/search/` | Search indexed documents by natural-language query |
| GET | `/session/` | Get current session info |
| GET | `/images/{filename}` | Get a pre-signed S3 URL for a page image |

---

## ☁️ Deployment

The backend is set up for serverless deployment on AWS via **SAM** (`backend/template.yaml`):

- `ApiFunction` — the FastAPI app running behind a Lambda Function URL (via `mangum`)
- `ExpiredDocsCleanupFunction` — runs every 2 hours to purge expired documents
- `OrphanS3CleanupFunction` — runs daily to remove orphaned S3 files

Deploy with the AWS SAM CLI:

```bash
cd backend
sam build
sam deploy --guided
```

You'll be prompted for `QdrantUrl`, `QdrantApiKey`, and `S3BucketName` as stack parameters. Update the CORS `AllowOrigins` in `template.yaml` to match your deployed frontend domain before deploying to production.

---

## 🗺️ Roadmap

- [ ] Add authentication beyond anonymous signed IDs (optional real accounts)
- [ ] Support additional document types beyond PDF
- [ ] Add automated tests for backend routes and ingestion pipeline
- [ ] CI/CD pipeline for backend (SAM) and frontend deploys

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 📄 License

No license is currently specified. Consider adding one (e.g. MIT) if you'd like others to reuse or contribute to this project.

---

## 🙏 Acknowledgements

- [ColPali](https://github.com/illuin-tech/colpali) — Efficient Document Retrieval with Vision Language Models
- [Qdrant](https://qdrant.tech/) — vector database used for multi-vector search
