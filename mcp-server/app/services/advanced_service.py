from app.utils.logger import logger
from app.utils import store


class AdvancedService:
    @staticmethod
    def map_business_context(requirement_id: str) -> dict:
        logger.info(f"Mapping business context for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        context, domain = _infer_context(requirement.get("query", ""))
        return {
            "requirement_id": requirement_id,
            "context": context,
            "domain": domain,
        }

    @staticmethod
    def generate_tests(plan_id: str) -> dict:
        logger.info(f"Generating tests for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        tests = _tests_from_components(plan.get("components_json") or [])
        return {
            "plan_id": plan_id,
            "tests_generated": tests,
        }

    @staticmethod
    def enforce_policy(plan_id: str) -> dict:
        logger.info(f"Enforcing policy for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        risk = plan.get("risk_level") or "Unknown"
        policy_passed = risk in ("Low", "Medium")
        policies = ["code_coverage", "naming_convention", "security_scan"]
        if risk == "High":
            policies.append("manual_security_review")
        return {
            "plan_id": plan_id,
            "policy_passed": policy_passed,
            "policies_checked": policies,
        }


def _infer_context(query: str) -> tuple[str, str]:
    text = query.lower()
    if any(word in text for word in ["b2b", "enterprise", "sso"]):
        return "Enterprise B2B flow", "authentication"
    if any(word in text for word in ["consumer", "mobile", "signup"]):
        return "Consumer onboarding", "growth"
    if any(word in text for word in ["billing", "invoice", "payment"]):
        return "Payments and billing", "finance"
    return "General product flow", "platform"


def _tests_from_components(components: list[str]) -> list[str]:
    tests = []
    if "auth_module" in components:
        tests.append("test_auth_module.py")
    if "database_schema" in components:
        tests.append("test_schema_migration.py")
    if "api_gateway" in components:
        tests.append("test_api_routes.py")
    if "frontend" in components:
        tests.append("test_ui_flows.py")
    if "infrastructure" in components:
        tests.append("test_deployment_pipeline.py")
    if not tests:
        tests.append("test_general_flow.py")
    return tests
