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
    def request_project_snapshot(requirement_id: str, root_path: str, mode: str = "full") -> dict:
        logger.info(f"Requesting project snapshot for {requirement_id} at {root_path} mode={mode}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        snapshot_id = str(uuid.uuid4())
        store.create_project_snapshot(snapshot_id, requirement_id, root_path, [])
        if mode == "light":
            instructions = {
                "powershell": (
                    f'$root="{root_path}"; '
                    'Get-ChildItem -Path $root -Directory | Select-Object -ExpandProperty FullName; '
                    'Get-ChildItem -Path $root -Recurse -File -Include '
                    'package.json,pyproject.toml,requirements.txt,package-lock.json,'
                    'pnpm-lock.yaml,poetry.lock,Pipfile,Pipfile.lock,*.csproj,*.sln,'
                    '*.yaml,*.yml,Dockerfile,*.tf,*.tfvars,go.mod,go.sum,'
                    'Cargo.toml,Cargo.lock,pom.xml,build.gradle,gradle.properties '
                    '| Select-Object -ExpandProperty FullName'
                ),
                "bash": (
                    f'root="{root_path}"; '
                    'find "$root" -maxdepth 2 -type d; '
                    'find "$root" -type f \\( '
                    '-name "package.json" -o -name "pyproject.toml" -o -name "requirements.txt" '
                    '-o -name "package-lock.json" -o -name "pnpm-lock.yaml" -o -name "poetry.lock" '
                    '-o -name "Pipfile" -o -name "Pipfile.lock" -o -name "*.csproj" -o -name "*.sln" '
                    '-o -name "*.yaml" -o -name "*.yml" -o -name "Dockerfile" -o -name "*.tf" '
                    '-o -name "*.tfvars" -o -name "go.mod" -o -name "go.sum" -o -name "Cargo.toml" '
                    '-o -name "Cargo.lock" -o -name "pom.xml" -o -name "build.gradle" '
                    '-o -name "gradle.properties" \\)'
                ),
            }
        else:
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
            "mode": mode,
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

    @staticmethod
    def start_project_interview(requirement_id: str) -> dict:
        logger.info(f"Starting project interview for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        questions = [
            {"id": "project_type", "question": "What type of product is this (web app, API, mobile, data pipeline, etc.)?"},
            {"id": "primary_language", "question": "Primary languages or runtimes used?"},
            {"id": "frameworks", "question": "Key frameworks/libraries (e.g., FastAPI, Django, React, Spring, etc.)?"},
            {"id": "services", "question": "List main services/modules and their purpose."},
            {"id": "data_stores", "question": "Databases/queues/storage used (Postgres, Redis, S3, Kafka, etc.)?"},
            {"id": "deploy_stack", "question": "How is it deployed (Docker, K8s, serverless, VM, CI/CD)?"},
            {"id": "integrations", "question": "External APIs or integrations?"},
            {"id": "constraints", "question": "Any constraints (latency, compliance, cost, timeline)?"},
        ]
        return {
            "requirement_id": requirement_id,
            "interview_id": str(uuid.uuid4()),
            "questions": questions,
            "next_step": "Collect answers and call submit_project_interview with the answers object.",
        }

    @staticmethod
    def submit_project_interview(requirement_id: str, answers: dict) -> dict:
        logger.info(f"Submitting project interview for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        store.save_answers(requirement_id, answers)
        llm_data = infer_universal(requirement.get("query", ""), {"interview_answers": answers})
        store.update_requirement(
            requirement_id,
            components_json=llm_data.get("components"),
            summary=llm_data.get("summary"),
            change_type=llm_data.get("change_type"),
            complexity=llm_data.get("complexity"),
        )
        return {
            "requirement_id": requirement_id,
            "components": llm_data.get("components"),
            "summary": llm_data.get("summary"),
            "change_type": llm_data.get("change_type"),
            "complexity": llm_data.get("complexity"),
        }

    @staticmethod
    def request_project_files(requirement_id: str, reason: str | None = None, suggested_paths: list[str] | None = None) -> dict:
        logger.info(f"Requesting project files for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        request_id = str(uuid.uuid4())
        paths = suggested_paths or []
        store.create_file_request(request_id, requirement_id, "file_list", paths)
        instructions = {
            "note": "Please send only the specific files relevant to the reason.",
            "example_paths": paths,
        }
        return {
            "requirement_id": requirement_id,
            "request_id": request_id,
            "reason": reason or "Need targeted files to improve analysis.",
            "instructions": instructions,
            "next_step": "Call submit_project_files with a list of relevant file paths.",
        }

    @staticmethod
    def submit_project_files(requirement_id: str, files: list[str]) -> dict:
        logger.info(f"Submitting project files for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        trimmed = files[:500]
        llm_data = infer_universal(requirement.get("query", ""), {"file_paths": trimmed})
        store.update_requirement(
            requirement_id,
            components_json=llm_data.get("components"),
            summary=llm_data.get("summary"),
            change_type=llm_data.get("change_type"),
            complexity=llm_data.get("complexity"),
        )
        return {
            "requirement_id": requirement_id,
            "files_received": len(files),
            "components": llm_data.get("components"),
            "summary": llm_data.get("summary"),
        }

    @staticmethod
    def request_file_contents(requirement_id: str, paths: list[str], reason: str | None = None) -> dict:
        logger.info(f"Requesting file contents for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        request_id = str(uuid.uuid4())
        store.create_file_request(request_id, requirement_id, "file_contents", paths)
        instructions = {
            "note": "Please send only the requested file contents (or relevant excerpts).",
            "paths": paths,
        }
        return {
            "requirement_id": requirement_id,
            "request_id": request_id,
            "reason": reason or "Need specific file content to refine analysis.",
            "instructions": instructions,
            "next_step": "Call submit_file_contents with a map of path -> content.",
        }

    @staticmethod
    def submit_file_contents(requirement_id: str, files: dict) -> dict:
        logger.info(f"Submitting file contents for {requirement_id}")
        requirement = store.get_requirement(requirement_id)
        if not requirement:
            return {"error": "Requirement not found", "requirement_id": requirement_id}
        saved = 0
        for path, content in files.items():
            if content:
                store.create_file_content(str(uuid.uuid4()), requirement_id, path, content[:20000])
                saved += 1
        llm_data = infer_universal(requirement.get("query", ""), {"file_contents": files})
        store.update_requirement(
            requirement_id,
            components_json=llm_data.get("components"),
            summary=llm_data.get("summary"),
            change_type=llm_data.get("change_type"),
            complexity=llm_data.get("complexity"),
        )
        return {
            "requirement_id": requirement_id,
            "files_received": saved,
            "components": llm_data.get("components"),
            "summary": llm_data.get("summary"),
        }
