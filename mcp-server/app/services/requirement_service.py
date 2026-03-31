import re
import uuid
from typing import Dict, Any, List

from app.utils.logger import logger
from app.utils import store


class RequirementService:
    @staticmethod
    def analyze_requirement_raw(query: str) -> dict:
        logger.info(f"Analyzing requirement: {query}")
        req_id = str(uuid.uuid4())
        summary = _summarize(query)
        complexity = _estimate_complexity(query)
        record = store.create_requirement(req_id, query, summary, complexity)
        return {
            "requirement_id": req_id,
            "summary": summary,
            "original_query": query,
            "complexity": complexity,
            "created_at": record.get("created_at"),
        }

    @staticmethod
    def generate_clarification_questions(req_id: str) -> dict:
        logger.info(f"Generating questions for requirement {req_id}")
        requirement = store.get_requirement(req_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": req_id}
        questions = _clarification_questions(requirement.get("query", ""))
        record = store.save_questions(req_id, questions) or {}
        return {
            "requirement_id": req_id,
            "questions": questions,
            "updated_at": record.get("updated_at"),
        }

    @staticmethod
    def merge_clarifications_raw(requirement_id: str, answers: dict) -> dict:
        logger.info(f"Merging clarifications for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        record = store.save_answers(requirement_id, answers) or {}
        return {
            "requirement_id": requirement_id,
            "merged": True,
            "answer_count": len(answers),
            "updated_at": record.get("updated_at"),
        }

    @staticmethod
    def classify_change_type(req_id: str) -> dict:
        logger.info(f"Classifying change type for {req_id}")
        requirement = store.get_requirement(req_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": req_id}
        change_type = _classify_change_type(requirement.get("query", ""))
        record = store.update_requirement(req_id, change_type=change_type) or {}
        return {"requirement_id": req_id, "change_type": change_type}


def _summarize(query: str) -> str:
    cleaned = " ".join(query.strip().split())
    if not cleaned:
        return "Empty requirement."
    if len(cleaned) <= 120:
        return cleaned
    # Prefer first sentence when available
    match = re.split(r"[.!?]", cleaned, maxsplit=1)
    summary = match[0] if match and match[0] else cleaned[:120]
    return summary.strip()


def _estimate_complexity(query: str) -> str:
    text = query.lower()
    score = 0
    if len(text.split()) > 40:
        score += 2
    if len(text.split()) > 80:
        score += 2
    keywords = ["realtime", "multi-tenant", "migration", "scalable", "distributed", "ml", "stream"]
    score += sum(1 for kw in keywords if kw in text)
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _classify_change_type(query: str) -> str:
    text = query.lower()
    if any(word in text for word in ["bug", "fix", "issue", "regression"]):
        return "bug"
    if any(word in text for word in ["schema", "migration", "database", "table"]):
        return "schema"
    if any(word in text for word in ["infra", "deployment", "k8s", "kubernetes", "aws", "terraform"]):
        return "infra"
    return "feature"


def _clarification_questions(query: str) -> list[dict]:
    questions = []
    def add(text: str) -> None:
        questions.append({"question_id": str(uuid.uuid4()), "text": text})

    text = query.lower()
    if "realtime" in text:
        add("What latency target defines realtime for this use case (e.g., <200ms, <1s)?")
    if any(word in text for word in ["auth", "login", "oauth", "sso"]):
        add("Which auth mechanisms must be supported (OAuth, SSO, API keys, etc.)?")
    if any(word in text for word in ["database", "schema", "migration"]):
        add("Which database engine and version are in scope, and can we run migrations online?")
    if any(word in text for word in ["api", "endpoint", "webhook"]):
        add("Which external APIs or integrations must this connect to?")
    add("What are the success metrics and acceptance criteria?")
    add("What are the highest-risk edge cases we must cover?")
    add("Are there performance or cost constraints we need to respect?")
    return questions[:5]
