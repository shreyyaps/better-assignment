# AI Email Assistant Monorepo

Production-ready monorepo skeleton for an AI Email Assistant.

## Structure

```
ai-email-assistant/
├── apps/
│   ├── backend/
│   └── frontend/
├── packages/
│   └── shared-types/
├── infra/
└── README.md
```

## Backend

### Setup

```
cd apps/backend
cp .env.example .env
uv venv
uv pip install .
python main.py
```

### Notes

- Flask app uses layered architecture with services and repositories.
- APScheduler runs a polling sync every 5 minutes.
- LangGraph orchestration is stubbed in `app/orchestration/email_graph.py`.
- Clerk JWT verification is in `app/auth/clerk_middleware.py`.

## Frontend

### Setup

```
cd apps/frontend
cp .env.example .env
npm install
npm run dev
```

## Infra

Start Postgres locally:

```
cd infra
docker compose up -d
```

## TODOs

- Replace Gmail API stub with real inbox + spam sync.
- Add Alembic migrations.
- Implement Gemini API calls.
- Implement Playwright unsubscribe flow.
- Add distributed locking for polling jobs.
# better-assignment
