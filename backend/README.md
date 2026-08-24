# D2A Backend

FastAPI service for the D2A MVP.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API

- `GET /health`
- `POST /api/auth/login`
- `GET /api/dashboard`
- `GET /api/records`
- `GET /api/alerts`
- `GET /api/insights`

The current implementation uses deterministic synthetic data so the frontend works immediately.

## AI Services

The AI/backend-services work lives in:

```text
app/services/
```

Main service entry point:

```python
from app.services.ai_pipeline import run_ai_pipeline
```

Tracing flow:

```text
records -> anomalies -> forecast -> alerts -> insights -> trace
```

See `../docs/backend-ai-services.md` for the collaboration split.
