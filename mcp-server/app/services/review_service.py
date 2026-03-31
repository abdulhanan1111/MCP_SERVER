import uuid

from app.config import settings
from app.utils.logger import logger
from app.utils import store


class ReviewService:
    @staticmethod
    def prepare_change_summary(plan_id: str) -> dict:
        logger.info(f"Preparing summary for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        requirement = store.get_requirement(plan.get("requirement_id"))
        summary = _build_summary(requirement, plan)
        return {
            "plan_id": plan_id,
            "summary": summary,
        }

    @staticmethod
    def prepare_diff_review(plan_id: str) -> dict:
        logger.info(f"Preparing diff review for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        diff, files, impact, assumptions = _build_diff_review(plan)
        return {
            "plan_id": plan_id,
            "diff": diff,
            "files": files,
            "impact": impact,
            "assumptions": assumptions,
        }

    @staticmethod
    def detect_sensitive_change(diff: str) -> dict:
        logger.info("Detecting sensitive changes in diff")
        sensitive_keywords = ["password", "secret", "token", "api_key", "private_key"]
        found = [kw for kw in sensitive_keywords if kw in diff.lower()]
        return {
            "is_sensitive": len(found) > 0,
            "reasons": [f"Found sensitive keyword: {kw}" for kw in found] if found else [],
        }

    @staticmethod
    def request_approval(plan_id: str) -> dict:
        logger.info(f"Requesting approval for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        auto_approve = settings.AUTO_APPROVE
        if auto_approve:
            approved = True
            feedback = "Auto-approved by policy."
        else:
            approved = False
            feedback = "Approval requested. Awaiting human sign-off."
        approval = store.create_approval(str(uuid.uuid4()), plan_id, approved, feedback)
        return {
            "plan_id": plan_id,
            "approved": approval["approved"],
            "feedback": approval["feedback"],
        }


def _build_summary(requirement: dict | None, plan: dict) -> str:
    req_summary = requirement.get("summary") if requirement else "No requirement summary available."
    steps = plan.get("steps_json") or []
    components = plan.get("components_json") or []
    return f"{req_summary} Plan includes {len(steps)} steps focused on {', '.join(components)}."


def _build_diff_review(plan: dict) -> tuple[str, list[str], str, list[str]]:
    components = plan.get("components_json") or []
    files = []
    diff_chunks = []
    if "auth_module" in components:
        files.append("auth.py")
        diff_chunks.append("--- a/auth.py\n+++ b/auth.py\n@@ -10,6 +10,10 @@\n+ def update_auth_policy():\n+     pass\n")
    if "database_schema" in components:
        files.append("schema.sql")
        diff_chunks.append("--- a/schema.sql\n+++ b/schema.sql\n@@ -1,3 +1,6 @@\n+ -- Add columns for new requirement\n")
    if "api_gateway" in components:
        files.append("routes.py")
        diff_chunks.append("--- a/routes.py\n+++ b/routes.py\n@@ -20,6 +20,10 @@\n+ def new_endpoint():\n+     pass\n")
    if "frontend" in components:
        files.append("ui.tsx")
        diff_chunks.append("--- a/ui.tsx\n+++ b/ui.tsx\n@@ -5,6 +5,12 @@\n+ // Update UI flow\n")
    if not files:
        files.append("app.py")
        diff_chunks.append("--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,4 @@\n+ # Placeholder change\n")
    impact = "Moderate" if len(components) > 2 else "Minimal"
    assumptions = [
        "Latest main branch is checked out",
        "Deployment pipeline credentials are available",
    ]
    return "\n".join(diff_chunks).strip(), files, impact, assumptions
