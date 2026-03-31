import os
import uuid
from app.utils.logger import logger
from app.utils import store
from app.utils.llm import infer_universal

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))


class PlanningService:
    @staticmethod
    def identify_impacted_components(req_id: str) -> dict:
        logger.info(f"Identifying components for {req_id}")
        requirement = store.get_requirement(req_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": req_id}
        llm_data = infer_universal(requirement.get("query", ""))
        components = llm_data.get("components") or []
        record = store.save_components(req_id, components) or {}
        return {
            "requirement_id": req_id,
            "components": components,
            "updated_at": record.get("updated_at"),
        }

    @staticmethod
    def create_change_plan_raw(requirement_id: str, components: list[str]) -> dict:
        logger.info(f"Creating change plan for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        if not components:
            components = requirement.get("components_json") or []
        if not components:
            llm_data = infer_universal(requirement.get("query", ""))
            components = llm_data.get("components") or []
        stored_components = requirement.get("components_json") or []
        warning = None
        if stored_components and sorted(stored_components) != sorted(components):
            warning = "Provided components differ from stored requirement components. Using provided list."
        store.save_components(requirement_id, components)
        plan_id = str(uuid.uuid4())
        llm_data = infer_universal(requirement.get("query", ""))
        steps = llm_data.get("plan_steps") or ["Define requirements", "Implement changes", "Validate behavior"]
        record = store.create_plan(plan_id, requirement_id, components, steps)
        return {
            "plan_id": plan_id,
            "requirement_id": requirement_id,
            "components": components,
            "steps": steps,
            "created_at": record.get("created_at"),
            "warning": warning,
        }

    @staticmethod
    def estimate_risk(plan_id: str) -> dict:
        logger.info(f"Estimating risk for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        requirement = store.get_requirement(plan.get("requirement_id"))
        llm_data = infer_universal((requirement or {}).get("query", ""))
        risk_level = llm_data.get("risk_level") or "Medium"
        factors = llm_data.get("risk_factors") or ["LLM provided no factors"]
        record = store.update_plan(plan_id, risk_level=risk_level, risk_factors_json=factors) or {}
        return {
            "plan_id": plan_id,
            "risk_level": risk_level,
            "factors": factors,
            "updated_at": record.get("updated_at"),
        }

    @staticmethod
    def validate_preconditions(plan_id: str) -> dict:
        logger.info(f"Validating preconditions for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        checks = _precondition_checks()
        valid = all(item["ok"] for item in checks)
        details = "All preconditions met." if valid else "Some preconditions failed."
        return {
            "plan_id": plan_id,
            "valid": valid,
            "details": details,
            "checks": checks,
        }


def _precondition_checks() -> list[dict]:
    checks = []
    checks.append({
        "check": "pyproject.toml exists",
        "ok": os.path.exists(os.path.join(PROJECT_ROOT, "pyproject.toml")) or os.path.exists(os.path.join(BASE_DIR, "pyproject.toml")),
    })
    checks.append({
        "check": "server.py exists",
        "ok": os.path.exists(os.path.join(BASE_DIR, "server.py")) or os.path.exists(os.path.join(PROJECT_ROOT, "mcp-server", "server.py")),
    })
    checks.append({
        "check": "requirements.txt exists",
        "ok": os.path.exists(os.path.join(BASE_DIR, "requirements.txt")) or os.path.exists(os.path.join(PROJECT_ROOT, "mcp-server", "requirements.txt")),
    })
    return checks
