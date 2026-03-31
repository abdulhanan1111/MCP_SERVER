from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Requirement Schemas ---
class RequirementRequest(BaseModel):
    query: str

class RequirementResponse(BaseModel):
    requirement_id: str
    structured_content: Dict[str, Any]

class ClarificationQuestion(BaseModel):
    question_id: str
    question_text: str

class ClarificationQuestionsResponse(BaseModel):
    questions: List[ClarificationQuestion]

class ClarificationMergeRequest(BaseModel):
    requirement_id: str
    answers: Dict[str, str]

class ChangeTypeResponse(BaseModel):
    change_type: str = Field(..., description="feature, bug, schema, or infra")

# --- Planning Schemas ---
class ImpactedComponentsRequest(BaseModel):
    requirement_id: str

class ImpactedComponentsResponse(BaseModel):
    components: List[str]

class ChangePlanRequest(BaseModel):
    requirement_id: str
    components: List[str]

class ChangePlanResponse(BaseModel):
    plan_id: str
    steps: List[str]

class RiskEstimateRequest(BaseModel):
    plan_id: str

class RiskEstimateResponse(BaseModel):
    risk_level: str
    factors: List[str]

class PreconditionRequest(BaseModel):
    plan_id: str

class PreconditionResponse(BaseModel):
    valid: bool
    details: str

# --- Review Schemas ---
class SummaryRequest(BaseModel):
    plan_id: str

class SummaryResponse(BaseModel):
    summary: str

class DiffReviewRequest(BaseModel):
    plan_id: str

class DiffReviewResponse(BaseModel):
    diff: str
    files: List[str]
    impact: str
    assumptions: List[str]

class SensitiveChangeRequest(BaseModel):
    diff: str

class SensitiveChangeResponse(BaseModel):
    is_sensitive: bool
    reasons: List[str]

class ApprovalRequestPayload(BaseModel):
    plan_id: str

class ApprovalResponse(BaseModel):
    approved: bool
    feedback: Optional[str] = None

# --- Execution Schemas ---
class ApplyChangeRequest(BaseModel):
    plan_id: str

class RollbackCreateRequest(BaseModel):
    plan_id: str

class RollbackCreateResponse(BaseModel):
    rollback_id: str

class RollbackExecuteRequest(BaseModel):
    rollback_id: str

class AuditLogEntry(BaseModel):
    action: str
    details: Dict[str, Any]

# --- Deployment Schemas ---
class ValidateRequest(BaseModel):
    plan_id: str

class GateDeploymentRequest(BaseModel):
    plan_id: str

class DeployRequestPayload(BaseModel):
    plan_id: str

class VerifyDeploymentRequestPayload(BaseModel):
    plan_id: str

class PromoteStopRequestPayload(BaseModel):
    plan_id: str
    action: str = Field(..., description="'promote' or 'stop'")

# --- Advanced Schemas ---
class MapBusinessContextRequest(BaseModel):
    requirement_id: str

class GenerateTestsRequest(BaseModel):
    plan_id: str

class EnforcePolicyRequest(BaseModel):
    plan_id: str
