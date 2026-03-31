import json
import os
import re
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.utils.logger import logger


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def infer_universal(query: str, answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not settings.GROQ_API_KEY:
        return {
            "error": "GROQ_API_KEY not set",
            "summary": query.strip()[:160] or "Empty requirement.",
            "change_type": "feature",
            "components": [],
            "plan_steps": ["Define requirements", "Implement changes", "Validate behavior"],
            "risk_level": "Medium",
            "risk_factors": ["LLM unavailable; using defaults"],
            "business_context": "General product flow",
            "domain": "platform",
            "tests": ["test_general_flow.py"],
            "complexity": "medium",
        }

    messages = _build_messages(query, answers)
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    timeout = httpx.Timeout(settings.LLM_TIMEOUT, read=settings.LLM_TIMEOUT)
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(GROQ_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = _parse_json(content)
            return _normalize_output(parsed)
    except Exception as exc:
        logger.error(f"LLM inference failed: {exc}")
        return {
            "error": "LLM inference failed",
            "summary": query.strip()[:160] or "Empty requirement.",
            "change_type": "feature",
            "components": [],
            "plan_steps": ["Define requirements", "Implement changes", "Validate behavior"],
            "risk_level": "Medium",
            "risk_factors": ["LLM call failed; using defaults"],
            "business_context": "General product flow",
            "domain": "platform",
            "tests": ["test_general_flow.py"],
            "complexity": "medium",
        }


def _build_messages(query: str, answers: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    system = (
        "You are a senior software architect. "
        "Return only valid JSON with the required fields. "
        "Fields: summary, change_type, components, plan_steps, risk_level, "
        "risk_factors, business_context, domain, tests, complexity. "
        "Use concise strings and lists of strings. "
        "Valid change_type: feature, bug, schema, infra, other. "
        "Valid risk_level: Low, Medium, High. "
        "Complexity: low, medium, high."
    )
    user = f"Requirement: {query.strip()}"
    if answers:
        user += f"\nClarifications: {json.dumps(answers)}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _parse_json(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _normalize_output(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "summary": _as_str(data.get("summary")),
        "change_type": _as_str(data.get("change_type", "feature")),
        "components": _as_list(data.get("components")),
        "plan_steps": _as_list(data.get("plan_steps")),
        "risk_level": _as_str(data.get("risk_level", "Medium")),
        "risk_factors": _as_list(data.get("risk_factors")),
        "business_context": _as_str(data.get("business_context", "General product flow")),
        "domain": _as_str(data.get("domain", "platform")),
        "tests": _as_list(data.get("tests")),
        "complexity": _as_str(data.get("complexity", "medium")),
    }


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return []
