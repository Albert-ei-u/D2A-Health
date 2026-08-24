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
