import json
import logging
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


logger = logging.getLogger(__name__)

GEMINI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "confidence": {"type": "number"},
    },
    "required": ["title", "summary", "recommendations", "confidence"],
}


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

    parsed_text = _extract_json_object(response_text)
    try:
        parsed = json.loads(parsed_text)
    except json.JSONDecodeError:
        parsed_lines = _parse_line_response(response_text)
        if parsed_lines:
            return GeminiInsightResult(
                title=parsed_lines["title"],
                summary=parsed_lines["summary"],
                recommendations=parsed_lines["recommendations"],
                confidence=0.7,
                model=settings.gemini_model,
            )

        partial_json = _parse_partial_json(response_text)
        if partial_json:
            return partial_json

        logger.warning("Gemini returned non-JSON text: %s", response_text[:300])
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

    recommendations = parsed.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    return GeminiInsightResult(
        title=str(parsed.get("title") or "Gemini recommendation"),
        summary=str(parsed.get("summary") or response_text.strip()[:500]),
        recommendations=[str(item) for item in recommendations[:4]],
        confidence=_bounded_confidence(parsed.get("confidence", 0.68)),
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
            "maxOutputTokens": 500,
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
        "aggregate synthetic data. Do not infer individual patient details. "
        "Return exactly five lines using this format:\n"
        "TITLE: short title\n"
        "SUMMARY: two concise sentences\n"
        "RECOMMENDATION 1: practical district health action\n"
        "RECOMMENDATION 2: practical district health action\n"
        "RECOMMENDATION 3: practical district health action\n\n"
        f"Dashboard context:\n{json.dumps(context, indent=2)}"
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


def _parse_partial_json(text: str) -> GeminiInsightResult | None:
    title = _extract_json_string_value(text, "title")
    summary = _extract_json_string_value(text, "summary")
    if not title or not summary:
        return None

    return GeminiInsightResult(
        title=title,
        summary=summary,
        recommendations=[
            "Validate Gemini's recommendation with facility-level evidence.",
            "Compare with staffing, supplies, and local surveillance.",
            "Use this as decision support, not an automated clinical decision.",
        ],
        confidence=0.66,
        model=settings.gemini_model,
        raw_preview=text.strip()[:220],
    )


def _extract_json_string_value(text: str, key: str) -> str | None:
    marker = f'"{key}"'
    marker_index = text.find(marker)
    if marker_index == -1:
        return None
    colon_index = text.find(":", marker_index + len(marker))
    if colon_index == -1:
        return None
    first_quote = text.find('"', colon_index + 1)
    if first_quote == -1:
        return None

    chars: list[str] = []
    escaped = False
    for char in text[first_quote + 1 :]:
        if escaped:
            chars.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            break
        else:
            chars.append(char)

    value = "".join(chars).strip()
    return value or None
