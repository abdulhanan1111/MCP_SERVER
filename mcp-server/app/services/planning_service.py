import uuid
from app.utils.logger import logger
from app.utils import store


class PlanningService:
    @staticmethod
    def identify_impacted_components(req_id: str) -> dict:
        logger.info(f"Identifying components for {req_id}")
        requirement = store.get_requirement(req_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": req_id}
        components = _components_from_text(requirement.get("query", ""))
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
        plan_id = str(uuid.uuid4())
        steps = _plan_steps(components)
        record = store.create_plan(plan_id, requirement_id, components, steps)
        return {
            "plan_id": plan_id,
            "requirement_id": requirement_id,
            "components": components,
            "steps": steps,
            "created_at": record.get("created_at"),
        }

    @staticmethod
    def estimate_risk(plan_id: str) -> dict:
        logger.info(f"Estimating risk for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        components = plan.get("components_json") or []
        risk_level, factors = _estimate_risk(components)
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


def _components_from_text(query: str) -> list[str]:
    text = query.lower()
    components = set()
    if any(word in text for word in ["auth", "login", "oauth", "sso"]):
        components.add("auth_module")
    if any(word in text for word in ["database", "schema", "migration", "table"]):
        components.add("database_schema")
    if any(word in text for word in ["api", "endpoint", "gateway", "webhook"]):
        components.add("api_gateway")
    if any(word in text for word in ["ui", "frontend", "dashboard"]):
        components.add("frontend")
    if any(word in text for word in ["infra", "deploy", "k8s", "terraform", "aws"]):
        components.add("infrastructure")
    components.add("tests")
    return sorted(components)


def _plan_steps(components: list[str]) -> list[str]:
    steps = []
    if "database_schema" in components:
        steps.append("Update database schema and run migrations")
    if "auth_module" in components:
        steps.append("Update auth module logic and access controls")
    if "api_gateway" in components:
        steps.append("Update API gateway routes and contracts")
    if "frontend" in components:
        steps.append("Update frontend UI flows and validations")
    if "infrastructure" in components:
        steps.append("Adjust infrastructure configuration and deployment manifests")
    steps.append("Add unit and integration tests")
    steps.append("Run validations and rollout checklist")
    return steps


def _estimate_risk(components: list[str]) -> tuple[str, list[str]]:
    factors = []
    score = 0
    if "database_schema" in components:
        factors.append("Schema migration required")
        score += 2
    if "api_gateway" in components:
        factors.append("API contract changes may affect clients")
        score += 1
    if "infrastructure" in components:
        factors.append("Infrastructure changes can impact stability")
        score += 2
    if "auth_module" in components:
        factors.append("Auth changes affect security boundaries")
        score += 1
    if score >= 4:
        return "High", factors
    if score >= 2:
        return "Medium", factors
    return "Low", factors or ["Low impact changes"]


def _precondition_checks() -> list[dict]:
    import os
    checks = []
    checks.append({"check": "pyproject.toml exists", "ok": os.path.exists("pyproject.toml")})
    checks.append({"check": "server.py exists", "ok": os.path.exists("mcp-server/server.py")})
    checks.append({"check": "requirements.txt exists", "ok": os.path.exists("mcp-server/requirements.txt")})
    return checks
