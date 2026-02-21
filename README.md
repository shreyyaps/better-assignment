# AI Browser Agent Monorepo

An AI‑assisted browser automation app. Users give a natural‑language objective, the system generates a multi‑step plan with Gemini, executes it in Playwright, and streams live progress to a chat‑style UI. Task history is stored in Postgres and secured with Clerk auth.

## Repo Structure

```
ai-email-assistant/
├── apps/
│   ├── backend/      # Flask + LangGraph + Playwright
│   └── frontend/     # React + Vite + Clerk
├── packages/
│   └── shared-types/
├── infra/            # Local Postgres
└── README.md
```

## Key Features

- Natural language → multi‑step browser plan (Gemini).
- Headed Playwright execution (you can watch it).
- Automatic retries with LLM replanning on failure.
- Real‑time event streaming via SSE.
- Chat‑style UI with task history sidebar.
- Task results persisted in Postgres.

## Architecture Overview

1. **Frontend**
   - User submits objective.
   - Opens SSE stream to backend.
   - Displays plan summary, live status, and screenshots.
   - Sidebar lists past tasks from DB.

2. **Backend**
   - Generates plan via Gemini.
   - Runs Playwright steps in a single session.
   - On failure: captures DOM + error → replans (up to N tries).
   - Streams events to frontend.
   - Saves final result in Postgres.

## Backend Setup

### Requirements

- Python 3.11+
- `uv`
- Postgres (via Docker in `infra/`)

### Install + Run

```
cd apps/backend
cp .env.example .env
uv venv
uv pip install .
uv run python -m playwright install
uv run python main.py
```

### Environment Variables

```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/ai_email
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-pro
CLERK_JWKS_URL=...

# Playwright controls
PLAYWRIGHT_HEADED=true
PLAYWRIGHT_SLOW_MO_MS=0
PLAYWRIGHT_DEFAULT_TIMEOUT_MS=3000
PLANNER_MAX_ATTEMPTS=3
```

## Frontend Setup

### Install + Run

```
cd apps/frontend
cp .env.example .env
npm install
npm run dev
```

### Environment Variables

```
VITE_CLERK_PUBLISHABLE_KEY=...
VITE_CLERK_JWT_TEMPLATE=backend
VITE_API_BASE_URL=http://localhost:8005
```

## API Endpoints

### Tasks

- `GET /tasks` – list tasks for user
- `GET /tasks/<id>` – get task details
- `POST /tasks/run` – run a task synchronously
- `POST /tasks/stream` – run a task with SSE streaming
- `POST /tasks/stop/<id>` – stop the active task session

### Streaming Events

Events emitted over SSE from `POST /tasks/stream`:

- `task` – contains `{ task_id }`
- `plan` – `{ summary }`
- `attempt_start`
- `step_start`
- `step_result`
- `step_error` – includes error + optional failure screenshot
- `replan`
- `complete` – final result summary + screenshot
- `error`
- `stopped`

## Design Decisions

- **LLM‑first orchestration**: Gemini creates structured step plans for Playwright.
- **Retry with context**: DOM snapshot + error are fed back to Gemini for replanning.
- **SSE streaming**: Lightweight real‑time updates without polling.
- **Headed browser**: Lets users observe automation for trust/debugging.
- **Minimal UI output**: Plan summary + screenshots, no raw JSON in the UI.

## Known Limitations

- CAPTCHA/anti‑bot systems will often block automation.
- In‑memory session tracking: active sessions are lost on backend restart.
- Selector reliability is LLM‑dependent and may break on UI changes.
- No domain allowlist or execution sandbox yet.

## Local Postgres (Infra)

```
cd infra
docker compose up -d
```

## Development Notes

- Backend entrypoint: `apps/backend/main.py`
- Playwright orchestration: `apps/backend/app/orchestration/browser_graph.py`
- Gemini client: `apps/backend/app/llm/gemini_client.py`
- Frontend UI: `apps/frontend/src/pages/Dashboard.tsx`

## Roadmap Ideas

- Persist step‑level events to DB.
- Allow domain allowlists and execution policies.
- Add OpenAI/Anthropic switchable LLM providers.
- Add video capture of Playwright sessions.

