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

## Tests

```bash
pytest
```

## Main routes

- `/api/auth/*` — login, invite admin, accept invite, me
- `/api/clerk/*` — stock entries, supply requests
- `/api/admin/*` — clerks, supply approve/decline, payments, clerk performance
- `/api/merchant/*` — admins, stores, store/product reports
- `/api/analytics/sales` — Chart.js-friendly sales series
