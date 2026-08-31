# MyDuka Backend

Flask inventory API for MyDuka (merchant / admin / clerk roles).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

API listens on `http://0.0.0.0:5000`. Health check: `GET /health`.

## Frontend connection

Set the frontend's `VITE_API_URL` to the API origin (for local development,
`http://localhost:5000`), then restart the Vite dev server. The backend loads
its `.env` file automatically. Set `CORS_ORIGINS` to the frontend origin (or a
comma-separated list of origins); it defaults to `FRONTEND_URL`.

## Tests

```bash
pytest
```

## Main routes

- `/api/auth/*` — merchant registration, login, invite admin, accept invite, me
- `/api/clerk/*` — stock entries, supply requests
- `/api/admin/*` — clerks, supply approve/decline, payments, clerk performance
- `/api/merchant/*` — admins, stores, store/product reports
- `/api/analytics/sales` — Chart.js-friendly sales series
