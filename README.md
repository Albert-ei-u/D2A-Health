# D2A Health

D2A, short for Data to Action, is an MVP health analytics platform for turning anonymized facility data into early warnings, trend summaries, and decision-support insights.

## Project Structure

```text
backend/    FastAPI API, synthetic data, analytics, alerts
frontend/   React + TypeScript dashboard
docs/       Project notes and architecture
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### Database and CSV testing

The backend uses `DATABASE_URL` from `backend/.env`. Verify the PostgreSQL connection with:

```bash
python -c "from sqlalchemy import text; from app.db import engine; connection=engine.connect(); print(connection.execute(text('SELECT 1')).scalar()); connection.close()"
```

Start the API and open `http://localhost:8000/docs`. Upload an anonymized CSV with
`POST /api/ingestion/patient-csv`. Accepted records are persisted in the
`patient_records` table and used by `/api/dashboard`, `/api/alerts`, `/api/insights`,
and `/api/ai/pipeline`. Delete the upload with `DELETE /api/ingestion/patient-csv`
to return to synthetic data.

The development login is configured with `DEMO_LOGIN_EMAIL` and
`DEMO_LOGIN_PASSWORD` in `.env`. The default values are `demo@d2a.health` and
`demo-password`. New accounts can be created with `POST /api/auth/signup` and
are stored in the `users` table with hashed passwords. This is an MVP login
contract, not production authentication.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## MVP Scope

- Anonymized synthetic patient records
- Facility-level dashboard summary
- Disease trend and patient-volume analytics
- Environmental context
- Early-warning alert generation
- Decision-support insights with evidence and confidence

This MVP is decision support only. It does not diagnose patients or replace healthcare professionals.
