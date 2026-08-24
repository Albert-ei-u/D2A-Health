# Backend AI Services Assignment

This is the backend area owned by the AI/services developer.

## Main Folder

```text
backend/app/services/
```

## Ownership

- `synthetic_data.py`: synthetic anonymized health and environmental data
- `analytics.py`: totals, trends, condition history, wait-pressure calculations
- `anomaly_detection.py`: disease anomaly scoring
- `forecasting.py`: next-week patient-volume forecast
- `recommendation_engine.py`: suggested operational considerations
- `alert_engine.py`: converts anomaly signals into early-warning alerts
- `insight_engine.py`: creates decision-support insights
- `ai_pipeline.py`: active tracing path for the full AI/service flow
- `tracing.py`: trace-step utilities

## Active Tracing Path

```text
build_patient_records()
  -> detect_condition_anomalies()
  -> forecast_total_volume()
  -> generate_alerts()
  -> generate_insights()
  -> run_ai_pipeline()
```

## Boundary With The Other Backend Developer

The other backend developer can own:

```text
backend/app/routers/
backend/app/models.py
backend/app/core/
backend/app/main.py
```

They should call service functions instead of putting analytics logic inside routes.

## Functions To Expose Through API Later

```python
run_ai_pipeline(records, environmental_signals)
generate_alerts(records)
generate_insights(records, environmental_signals)
detect_condition_anomalies(records)
forecast_total_volume(records)
```
