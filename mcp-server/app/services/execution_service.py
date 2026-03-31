import uuid

from app.utils.logger import logger
from app.utils import store


class ExecutionService:
    @staticmethod
    def apply_change(plan_id: str) -> dict:
        logger.info(f"Applying change for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        approval = store.get_latest_approval(plan_id)
        if not approval or not approval.get("approved"):
            return {
                "error": "Plan has not been approved",
                "plan_id": plan_id,
                "status": "blocked",
                "reason": approval.get("feedback") if approval else "No approval record",
            }
        exec_record = store.create_execution(
            str(uuid.uuid4()),
            plan_id,
            "apply_change",
            "success",
            {"components": plan.get("components_json") or []},
        )
        return {
            "plan_id": plan_id,
            "applied": True,
            "status": exec_record["status"],
            "execution_id": exec_record["execution_id"],
        }

    @staticmethod
    def create_rollback(plan_id: str) -> dict:
        logger.info(f"Creating rollback for plan {plan_id}")
        plan = store.get_plan(plan_id)
        if not plan:
            return {"error": "Plan not found", "plan_id": plan_id}
        rollback_id = str(uuid.uuid4())
        record = store.create_rollback(rollback_id, plan_id, "created")
        return {"plan_id": plan_id, "rollback_id": record["rollback_id"], "status": record["status"]}

    @staticmethod
    def rollback(rollback_id: str) -> dict:
        logger.info(f"Executing rollback {rollback_id}")
        record = store.update_rollback(rollback_id, "rolled_back")
        if not record:
            return {"error": "Rollback not found", "rollback_id": rollback_id}
        return {"rollback_id": rollback_id, "rolled_back": True, "status": record["status"]}

    @staticmethod
    def audit_log_raw(action: str, details: dict) -> dict:
        logger.info(f"AUDIT LOG | action={action} | details={details}")
        record = store.create_audit_log(str(uuid.uuid4()), action, details)
        return {"logged": True, "action": record["action"], "status": "success"}
