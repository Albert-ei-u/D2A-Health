# D2A Architecture

## Flow

```text
Frontend dashboard
  -> Backend API
    -> Synthetic/anonymized health records
    -> Validation and aggregation
    -> Trend and anomaly analysis
    -> Alert generation
    -> Decision-support insight generation
```

## Backend Modules

- `app.main`: FastAPI application and route registration
- `app.routers`: API endpoints for auth, dashboard, records, alerts, and insights
- `app.services.synthetic_data`: deterministic synthetic dataset
- `app.services.analytics`: aggregation and trend calculations
- `app.services.alert_engine`: early-warning rule engine
- `app.services.insight_engine`: human-readable decision-support outputs

## Frontend Views

- Login panel
- Dashboard summary
- Patient volume trends
- Disease trend chart
- Environmental context
- Early-warning alerts
- AI insights and recommendations

## Future Integration Points

- PostgreSQL persistence
- DHIS2/NHIC/EMR integration adapters
- Role-based access control
- Audit logging
- Model monitoring and feedback workflow
