import json
import logging
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeminiInsightResult:
    title: str
    summary: str
    recommendations: list[str]
    confidence: float
    model: str
    raw_preview: str | None = None


def generate_gemini_health_insight(context: dict[str, object]) -> GeminiInsightResult | None:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return None
    if not settings.gemini_api_key:
        logger.info("Gemini insight skipped because GEMINI_API_KEY is not configured.")
        return None

    response_text = _generate_content(_build_prompt(context))
    if not response_text:
        logger.warning("Gemini insight skipped because the API returned no usable text.")
        return None

    parsed_lines = _parse_line_response(response_text)
    if parsed_lines:
        return GeminiInsightResult(
            title=parsed_lines["title"],
            summary=parsed_lines["summary"],
            recommendations=parsed_lines["recommendations"],
            confidence=0.72,
            model=settings.gemini_model,
        )

    parsed_json = _parse_json_response(response_text)
    if parsed_json:
        return parsed_json

    logger.warning("Gemini returned an unparseable response: %s", response_text[:300])
    return GeminiInsightResult(
        title="Gemini recommendation",
        summary=response_text.strip()[:500],
        recommendations=[
            "Validate Gemini's recommendation with facility-level evidence.",
            "Use this as decision support, not an automated clinical decision.",
        ],
        confidence=0.62,
        model=settings.gemini_model,
        raw_preview=response_text.strip()[:220],
    )


def _generate_content(prompt: str) -> str | None:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{settings.gemini_model}:generateContent"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 220,
        },
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.gemini_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        logger.warning("Gemini HTTP error %s: %s", error.code, detail[:500])
        return None
    except URLError as error:
        logger.warning("Gemini URL error: %s", error)
        return None
    except TimeoutError:
        logger.warning("Gemini request timed out after %s seconds.", settings.gemini_timeout_seconds)
        return None
    except OSError as error:
        logger.warning("Gemini request failed: %s", error)
        return None
    except json.JSONDecodeError as error:
        logger.warning("Gemini returned invalid response JSON: %s", error)
        return None

    candidates = body.get("candidates", [])
    if not candidates:
        logger.warning("Gemini response had no candidates: %s", json.dumps(body)[:500])
        return None

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if "text" in part:
            text_parts.append(str(part["text"]))
        elif "json" in part:
            text_parts.append(json.dumps(part["json"]))
    text = "\n".join(part for part in text_parts if part).strip()
    return text or None


def _build_prompt(context: dict[str, object]) -> str:
    return (
        "You are supporting a public-health MVP dashboard using only anonymized, "
        "aggregate anonymized facility data. Do not infer individual patient details. "
        "Do not return JSON. Do not use braces. Return exactly five lines using this format:\n"
        "TITLE: short title\n"
        "SUMMARY: one sentence under 25 words\n"
        "RECOMMENDATION 1: action under 15 words\n"
        "RECOMMENDATION 2: action under 15 words\n"
        "RECOMMENDATION 3: action under 15 words\n\n"
        f"Dashboard context:\n{json.dumps(context, indent=2)}"
    )


def _parse_json_response(text: str) -> GeminiInsightResult | None:
    parsed_text = _extract_json_object(text)
    try:
        parsed = json.loads(parsed_text)
    except json.JSONDecodeError:
        return None

    recommendations = parsed.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    return GeminiInsightResult(
        title=str(parsed.get("title") or "Gemini recommendation"),
        summary=str(parsed.get("summary") or text.strip()[:500]),
        recommendations=[str(item) for item in recommendations[:4]]
        or [
            "Validate the AI recommendation with facility staff.",
            "Compare against local surveillance before escalation.",
        ],
        confidence=_bounded_confidence(parsed.get("confidence", 0.68)),
        model=settings.gemini_model,
    )


def _extract_json_object(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return cleaned
    return cleaned[start : end + 1]


def _bounded_confidence(value: object) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.68
    return round(min(max(confidence, 0), 1), 2)


def _parse_line_response(text: str) -> dict[str, object] | None:
    values: dict[str, str] = {}
    recommendations: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if not value:
            continue
        if key == "title":
            values["title"] = value
        elif key == "summary":
            values["summary"] = value
        elif key.startswith("recommendation"):
            recommendations.append(value)

    if not values.get("title") or not values.get("summary"):
        return None

    return {
        "title": values["title"],
        "summary": values["summary"],
        "recommendations": recommendations
        or [
            "Validate the AI recommendation with facility staff.",
            "Compare against local surveillance before escalation.",
        ],
    }
