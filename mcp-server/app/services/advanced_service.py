from app.utils.logger import logger
from app.utils import store
from app.utils.llm import infer_universal


class AdvancedService:
    @staticmethod
    def map_business_context(requirement_id: str) -> dict:
        logger.info(f"Mapping business context for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        llm_data = infer_universal(requirement.get("query", ""))
        context = llm_data.get("business_context")
        domain = llm_data.get("domain")
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
        requirement = store.get_requirement(plan.get("requirement_id"))
        llm_data = infer_universal((requirement or {}).get("query", ""))
        tests = llm_data.get("tests") or []
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
        response = {
            "plan_id": plan_id,
            "policy_passed": policy_passed,
            "policies_checked": policies,
        }
        if risk == "Unknown":
            response["warning"] = "Risk level not estimated. Run estimate_risk first."
        return response
