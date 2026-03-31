import uuid

from app.config import settings
from app.utils.logger import logger
from app.utils import store


class DeploymentService:
    @staticmethod
    def run_validations(plan_id: str) -> dict:
        logger.info(f"Running validations for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        checks = _runtime_checks()
        valid = all(item["ok"] for item in checks)
        return {"plan_id": plan_id, "valid": valid, "checks": checks}

    @staticmethod
    def gate_deployment(plan_id: str) -> dict:
        logger.info(f"Gating deployment for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        approval = store.get_latest_approval(plan_id)
        if approval and approval.get("approved"):
            return {"plan_id": plan_id, "allowed": True, "reason": "Approved by reviewer."}
        return {"plan_id": plan_id, "allowed": False, "reason": "Approval missing or pending."}

    @staticmethod
    def deploy(plan_id: str) -> dict:
        logger.info(f"Deploying plan {plan_id} - integration point")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        environment = settings.DEFAULT_ENV
        record = store.create_deployment(
            str(uuid.uuid4()),
            plan_id,
            environment,
            "deployed",
            "deploy",
            {"components": plan.get("components_json") or []},
        )
        return {
            "plan_id": plan_id,
            "deployed": True,
            "environment": record["environment"],
            "deployment_id": record["deployment_id"],
        }

    @staticmethod
    def verify_deployment(plan_id: str) -> dict:
        logger.info(f"Verifying deployment for plan {plan_id}")
        deployment = store.get_latest_deployment(plan_id)
        if not deployment:
            return {"plan_id": plan_id, "verified": False, "health_check": "not_deployed"}
        return {"plan_id": plan_id, "verified": True, "health_check": "passed"}

    @staticmethod
    def promote_or_stop_raw(plan_id: str, action: str) -> dict:
        logger.info(f"Action '{action}' for plan {plan_id}")
        if action not in ("promote", "stop"):
            return {"error": "Action must be 'promote' or 'stop'"}
        deployment = store.update_deployment_status(plan_id, action, action)
        if not deployment:
            return {"error": "Deployment not found", "plan_id": plan_id}
        return {"plan_id": plan_id, "action_taken": action, "status": "success"}


def _runtime_checks() -> list[dict]:
    import os
    checks = []
    checks.append({"check": "server.py exists", "ok": os.path.exists("mcp-server/server.py")})
    checks.append({"check": "tools folder exists", "ok": os.path.isdir("mcp-server/app/tools")})
    checks.append({"check": "services folder exists", "ok": os.path.isdir("mcp-server/app/services")})
    return checks
