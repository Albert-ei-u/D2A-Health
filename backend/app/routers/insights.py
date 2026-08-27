from fastapi import APIRouter, Header

from app.models import Insight
from app.services.dataset_store import require_user_dataset
from app.services.insight_engine import generate_insights

router = APIRouter()


@router.get("", response_model=list[Insight])
def list_insights(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> list[Insight]:
    records = require_user_dataset(x_user_email)
    return generate_insights(records, [])
