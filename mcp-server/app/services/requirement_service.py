import uuid

from app.utils.logger import logger
from app.utils import store
from app.utils.llm import infer_universal


class RequirementService:
    @staticmethod
    def analyze_requirement_raw(query: str) -> dict:
        logger.info(f"Analyzing requirement: {query}")
        req_id = str(uuid.uuid4())
        llm_data = infer_universal(query)
        summary = llm_data.get("summary") or query.strip()[:160]
        complexity = llm_data.get("complexity") or "medium"
        record = store.create_requirement(req_id, query, summary, complexity)
        store.update_requirement(
            req_id,
            change_type=llm_data.get("change_type"),
            components_json=llm_data.get("components"),
        )
        return {
            "requirement_id": req_id,
            "summary": summary,
            "original_query": query,
            "complexity": complexity,
            "created_at": record.get("created_at"),
            "change_type": llm_data.get("change_type"),
            "components": llm_data.get("components"),
        }

    @staticmethod
    def generate_clarification_questions(req_id: str) -> dict:
        logger.info(f"Generating questions for requirement {req_id}")
        requirement = store.get_requirement(req_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": req_id}
        questions = [
            {"question_id": str(uuid.uuid4()), "text": "What is the primary outcome or KPI?"},
            {"question_id": str(uuid.uuid4()), "text": "Who are the users and how will they use this?"},
            {"question_id": str(uuid.uuid4()), "text": "Are there performance or latency targets?"},
            {"question_id": str(uuid.uuid4()), "text": "What integrations or dependencies are required?"},
            {"question_id": str(uuid.uuid4()), "text": "Any constraints (budget, time, compliance)?"}
        ]
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
        llm_data = infer_universal(requirement.get("query", ""), answers)
        store.update_requirement(
            requirement_id,
            summary=llm_data.get("summary"),
            complexity=llm_data.get("complexity"),
            change_type=llm_data.get("change_type"),
            components_json=llm_data.get("components"),
        )
        return {
            "requirement_id": requirement_id,
            "merged": True,
            "answer_count": len(answers),
            "updated_at": record.get("updated_at"),
            "summary": llm_data.get("summary"),
            "complexity": llm_data.get("complexity"),
        }

    @staticmethod
    def classify_change_type(req_id: str) -> dict:
        logger.info(f"Classifying change type for {req_id}")
        requirement = store.get_requirement(req_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": req_id}
        llm_data = infer_universal(requirement.get("query", ""))
        store.update_requirement(
            req_id,
            change_type=llm_data.get("change_type"),
            components_json=llm_data.get("components"),
        )
        return {"requirement_id": req_id, "change_type": llm_data.get("change_type")}
