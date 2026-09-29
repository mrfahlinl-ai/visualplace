# VisualPlace

[![Repo](https://img.shields.io/badge/GitHub-visualplace-181717?logo=github)](https://github.com/mrfahlinl-ai/visualplace)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688?logo=fastapi)](https://fastapi.tiangolo.com)

**Find where a photo was taken.** VisualPlace is an evidence-based AI visual
geolocation tool. Instead of asking a model "where is this?" and trusting the
answer, it runs a transparent pipeline that gathers clues, generates candidate
locations, verifies them against maps and the web, scores the evidence, and
explains *why* it reached a conclusion — comfortable saying "I don't know" when
the evidence is weak.

```
IMAGE → ANALYSIS → CLUES → CANDIDATES → MAP/PLACE SEARCH
      → WEB/IMAGE VERIFICATION → SCORING → RESULT + EXPLANATION + MAP
```

## Architecture

| Layer     | Stack                                                        |
| --------- | ------------------------------------------------------------ |
| Frontend  | Next.js 16 (App Router), TypeScript, Tailwind CSS 4          |
| Backend   | FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2 (async)      |
| Database  | PostgreSQL 16                                                |
| Cache/jobs| Redis 7                                                      |
| AI vision | Provider abstraction — Anthropic Claude (default)            |
| Maps      | Provider abstraction — OpenStreetMap/Nominatim (default)     |
| Search    | Provider abstraction — optional, disabled by default         |

Every external capability sits behind an interface selected by environment
variables (`backend/app/services/providers/`), so no vendor is hard-coded.

```
VisualPlace/
├─ frontend/        Next.js app (UI)
├─ backend/         FastAPI app (pipeline, providers, API)
│  └─ app/{api,core,models,schemas,services,repositories}
├─ docker/          Dockerfiles
├─ docs/            Documentation (phase notes, architecture)
├─ scripts/         Dev helper scripts
├─ .env.example     All configuration, documented
└─ docker-compose.yml
```

## Requirements

- Node.js ≥ 20 (tested on 24)
- Python ≥ 3.12
- PostgreSQL 16 & Redis 7 (or Docker)

## Setup

```bash
cp .env.example .env   # fill in AI_API_KEY etc.
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  Unix: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

- API docs (non-production): http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:3000
```

### Docker (all services)

```bash
cp .env.example .env
docker compose up --build
```

## Commands

| Task              | Command                                             |
| ----------------- | --------------------------------------------------- |
| Backend dev       | `uvicorn app.main:app --reload` (in `backend/`)     |
| Backend tests     | `pytest` (in `backend/`)                            |
| Backend lint      | `ruff check app tests` · types: `mypy app`          |
| Frontend dev      | `npm run dev` (in `frontend/`)                      |
| Frontend build    | `npm run build`                                     |
| Frontend lint     | `npm run lint`                                       |

## Environment variables

See [`.env.example`](.env.example) — every setting is documented there.
Secrets (AI/map/search keys, DB URL) are **server-side only**; only
`NEXT_PUBLIC_*` values reach the browser.

## Development roadmap

Built in phases (see [`docs/`](docs/)):

1. ✅ Architecture + project initialization
2. ✅ Database + backend foundation
3. ✅ Image upload system
4. ✅ AI image analysis
5. ✅ EXIF + OCR
6. ✅ Candidate generation
7. ✅ Maps + place search
8. ✅ Candidate verification + finalize
9. ✅ Result UI
10. ✅ Security · 11. ✅ Testing · 12. ✅ Performance · 13. ✅ Deployment (Docker)

**Deployment:** see [`docs/DEPLOY.md`](docs/DEPLOY.md) (Docker Compose).

## Principles

- **No hallucinated locations.** Every conclusion is backed by evidence; the UI
  distinguishes GPS metadata, landmark matches, sign/business matches, and
  geographic inference — and shows a confidence grounded in evidence quality.
- **Privacy first.** Uploads are validated, processed privately, and deleted
  automatically. Images are not retained unless explicitly enabled.
- **Prompt-injection safe.** Text found inside an image is always treated as
  untrusted data, never as instructions.
