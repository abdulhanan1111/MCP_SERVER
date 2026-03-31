import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "app", "data", "mcp.db")

def _resolve_db_path() -> str:
    env_path = getattr(settings, "DB_PATH", None)
    if env_path:
        if os.path.isabs(env_path):
            return env_path
        return os.path.abspath(os.path.join(BASE_DIR, env_path))
    return os.path.abspath(DEFAULT_DB_PATH)


def _ensure_db_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _is_writable(path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        test_file = os.path.join(os.path.dirname(path), ".write_test")
        with open(test_file, "w", encoding="utf-8") as handle:
            handle.write("ok")
        os.remove(test_file)
        return True
    except Exception:
        return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    path = _resolve_db_path()
    if not _is_writable(path):
        fallback = os.path.join(os.path.abspath(os.getenv("TMP", "/tmp")), "mcp.db")
        path = fallback
    _ensure_db_dir(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS requirements (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                summary TEXT,
                complexity TEXT,
                change_type TEXT,
                components_json TEXT,
                clarifications_json TEXT,
                answers_json TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                components_json TEXT,
                steps_json TEXT,
                risk_level TEXT,
                risk_factors_json TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                approved INTEGER,
                feedback TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                action TEXT,
                status TEXT,
                details_json TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rollbacks (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                status TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS deployments (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                environment TEXT,
                status TEXT,
                action TEXT,
                details_json TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                action TEXT,
                details_json TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()


init_db()


def create_requirement(req_id: str, query: str, summary: str, complexity: str) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO requirements (id, query, summary, complexity, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (req_id, query, summary, complexity, now, now),
        )
        conn.commit()
    return get_requirement(req_id) or {}


def update_requirement(req_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    if not fields:
        return get_requirement(req_id)
    for key in ("components_json", "clarifications_json", "answers_json"):
        if key in fields and fields[key] is not None and not isinstance(fields[key], str):
            fields[key] = json.dumps(fields[key])
    fields["updated_at"] = _now_iso()
    columns = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values()) + [req_id]
    with _connect() as conn:
        conn.execute(f"UPDATE requirements SET {columns} WHERE id = ?", values)
        conn.commit()
    return get_requirement(req_id)


def get_requirement(req_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM requirements WHERE id = ?", (req_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_dict(row)


def save_questions(req_id: str, questions: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return update_requirement(req_id, clarifications_json=json.dumps(questions))


def save_answers(req_id: str, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return update_requirement(req_id, answers_json=json.dumps(answers))


def save_components(req_id: str, components: list[str]) -> Optional[Dict[str, Any]]:
    return update_requirement(req_id, components_json=components)


def create_plan(plan_id: str, requirement_id: str, components: list[str], steps: list[str]) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO plans (id, requirement_id, components_json, steps_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (plan_id, requirement_id, json.dumps(components), json.dumps(steps), now, now),
        )
        conn.commit()
    return get_plan(plan_id) or {}


def update_plan(plan_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    if not fields:
        return get_plan(plan_id)
    fields["updated_at"] = _now_iso()
    columns = ", ".join([f"{k} = ?" for k in fields.keys()])
    values = list(fields.values()) + [plan_id]
    with _connect() as conn:
        conn.execute(f"UPDATE plans SET {columns} WHERE id = ?", values)
        conn.commit()
    return get_plan(plan_id)


def get_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_dict(row)


def create_approval(approval_id: str, plan_id: str, approved: bool, feedback: str | None) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO approvals (id, plan_id, approved, feedback, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (approval_id, plan_id, 1 if approved else 0, feedback, now),
        )
        conn.commit()
    return {
        "approval_id": approval_id,
        "plan_id": plan_id,
        "approved": approved,
        "feedback": feedback,
        "created_at": now,
    }


def get_latest_approval(plan_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM approvals WHERE plan_id = ? ORDER BY created_at DESC LIMIT 1",
            (plan_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        data = _row_to_dict(row)
        data["approved"] = bool(data.get("approved"))
        return data


def create_execution(exec_id: str, plan_id: str, action: str, status: str, details: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO executions (id, plan_id, action, status, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (exec_id, plan_id, action, status, json.dumps(details), now),
        )
        conn.commit()
    return {
        "execution_id": exec_id,
        "plan_id": plan_id,
        "action": action,
        "status": status,
        "details": details,
        "created_at": now,
    }


def create_rollback(rollback_id: str, plan_id: str, status: str) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO rollbacks (id, plan_id, status, created_at) VALUES (?, ?, ?, ?)",
            (rollback_id, plan_id, status, now),
        )
        conn.commit()
    return {"rollback_id": rollback_id, "plan_id": plan_id, "status": status, "created_at": now}


def update_rollback(rollback_id: str, status: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        conn.execute("UPDATE rollbacks SET status = ? WHERE id = ?", (status, rollback_id))
        conn.commit()
        cur = conn.execute("SELECT * FROM rollbacks WHERE id = ?", (rollback_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_dict(row)


def create_deployment(deploy_id: str, plan_id: str, environment: str, status: str, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO deployments (id, plan_id, environment, status, action, details_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (deploy_id, plan_id, environment, status, action, json.dumps(details), now),
        )
        conn.commit()
    return {
        "deployment_id": deploy_id,
        "plan_id": plan_id,
        "environment": environment,
        "status": status,
        "action": action,
        "details": details,
        "created_at": now,
    }


def get_latest_deployment(plan_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT * FROM deployments WHERE plan_id = ? ORDER BY created_at DESC LIMIT 1",
            (plan_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_dict(row)


def update_deployment_status(plan_id: str, status: str, action: str) -> Optional[Dict[str, Any]]:
    latest = get_latest_deployment(plan_id)
    if not latest:
        return None
    with _connect() as conn:
        conn.execute(
            "UPDATE deployments SET status = ?, action = ? WHERE id = ?",
            (status, action, latest["id"]),
        )
        conn.commit()
    return get_latest_deployment(plan_id)


def create_audit_log(log_id: str, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
    now = _now_iso()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO audit_logs (id, action, details_json, created_at) VALUES (?, ?, ?, ?)",
            (log_id, action, json.dumps(details), now),
        )
        conn.commit()
    return {"audit_id": log_id, "action": action, "details": details, "created_at": now}


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    data = dict(row)
    for key in ("components_json", "steps_json", "risk_factors_json", "clarifications_json", "answers_json", "details_json"):
        if key in data and data[key]:
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                pass
    return data
