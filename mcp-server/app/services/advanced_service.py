import uuid

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

    @staticmethod
    def request_project_snapshot(requirement_id: str, root_path: str) -> dict:
        logger.info(f"Requesting project snapshot for {requirement_id} at {root_path}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        snapshot_id = str(uuid.uuid4())
        store.create_project_snapshot(snapshot_id, requirement_id, root_path, [])
        instructions = {
            "powershell": (
                f'Get-ChildItem -Recurse -File "{root_path}" | '
                "Select-Object -ExpandProperty FullName"
            ),
            "bash": (
                f'find "{root_path}" -type f'
            ),
        }
        return {
            "requirement_id": requirement_id,
            "snapshot_id": snapshot_id,
            "instructions": instructions,
            "next_step": "Run the command on the client machine and call submit_project_snapshot with the file list.",
        }

    @staticmethod
    def submit_project_snapshot(snapshot_id: str, file_list: list[str]) -> dict:
        logger.info(f"Submitting project snapshot {snapshot_id}")
        snapshot = store.get_project_snapshot(snapshot_id)
        if not snapshot:
            return {"error": "Snapshot not found", "snapshot_id": snapshot_id}
        trimmed = file_list[:2000]
        updated = store.update_project_snapshot(snapshot_id, trimmed) or {}
        requirement_id = updated.get("requirement_id")
        requirement = store.get_requirement(requirement_id) if requirement_id else None
        llm_data = infer_universal((requirement or {}).get("query", ""), {"file_list": trimmed})
        if requirement_id:
            store.update_requirement(
                requirement_id,
                components_json=llm_data.get("components"),
                summary=llm_data.get("summary"),
                change_type=llm_data.get("change_type"),
                complexity=llm_data.get("complexity"),
            )
        return {
            "snapshot_id": snapshot_id,
            "files_received": len(file_list),
            "components": llm_data.get("components"),
            "summary": llm_data.get("summary"),
        }
