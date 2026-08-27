from fastapi import APIRouter, Header

from app.models import Alert
from app.services.alert_engine import generate_alerts
from app.services.dataset_store import require_user_dataset

router = APIRouter()


@router.get("", response_model=list[Alert])
def list_alerts(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> list[Alert]:
    records = require_user_dataset(x_user_email)
    return generate_alerts(records, [])
