"""Pydantic schemas for API request/response validation."""

import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Phone number validation pattern: allows +country-code, digits, hyphens, spaces
PHONE_PATTERN = re.compile(r'^\+?[\d\s\-]{7,20}$')


# ── Request Schemas ──────────────────────────────────────────────

class CandidateApplyRequest(BaseModel):
    """Request to submit a candidate application."""
    name: str = Field(..., min_length=1, max_length=255, description="Candidate full name")
    phone: str = Field(..., min_length=7, max_length=20, description="Phone number (unique identifier)")
    skills: List[str] = Field(..., min_length=1, description="List of candidate skills")
    years_experience: int = Field(..., ge=0, le=50, description="Years of professional experience")
    location: str = Field(..., min_length=1, max_length=255, description="Candidate location")
    pitch: str = Field(..., min_length=10, max_length=1000, description="2-3 sentence pitch on why they are a fit")
    role_id: str = Field(..., min_length=1, description="Role ID to apply for")

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        v = v.strip()
        if not PHONE_PATTERN.match(v):
            raise ValueError(
                'Invalid phone number format. Use digits with optional +country code '
                'and hyphens (e.g., +91-9876543210 or 9876543210)'
            )
        return v

    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Strip whitespace from skills and remove empty ones."""
        cleaned = [s.strip() for s in v if s.strip()]
        if not cleaned:
            raise ValueError('At least one non-empty skill is required')
        return cleaned

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Strip and validate name."""
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        return v


class BucketOverrideRequest(BaseModel):
    """Request to override a candidate's bucket assignment."""
    application_id: int = Field(..., description="Application ID to override")
    new_bucket: str = Field(..., pattern="^(advance|hold|reject)$", description="New bucket: advance, hold, or reject")
    reason: str = Field(..., min_length=5, description="Mandatory reason for the override")
    overridden_by: str = Field(..., min_length=1, description="Name/ID of the recruiter making the override")


# ── Response Schemas ─────────────────────────────────────────────

class ConstraintResult(BaseModel):
    """Result of a single constraint check."""
    constraint: str
    passed: bool
    detail: str


class LLMEvaluation(BaseModel):
    """LLM evaluation results."""
    score: int = Field(..., ge=0, le=100)
    reasoning: str
    eligibility: str


class StageTransitionResponse(BaseModel):
    """A single stage transition entry."""
    from_stage: Optional[str]
    to_stage: str
    reason: str
    triggered_by: str
    timestamp: datetime

    class Config:
        from_attributes = True


class BucketOverrideResponse(BaseModel):
    """A single bucket override entry."""
    old_bucket: str
    new_bucket: str
    reason: str
    overridden_by: str
    timestamp: datetime

    class Config:
        from_attributes = True


class ApplicationResponse(BaseModel):
    """Full application details."""
    id: int
    role_id: str
    candidate_name: str
    candidate_phone: str
    skills: List[str]
    years_experience: int
    location: str
    pitch: str
    current_stage: str
    bucket: Optional[str]
    llm_score: Optional[int]
    llm_reasoning: Optional[str]
    constraint_results: Optional[List[ConstraintResult]]
    eligibility: Optional[str]
    created_at: datetime
    updated_at: datetime
    stage_transitions: List[StageTransitionResponse] = []
    bucket_overrides: List[BucketOverrideResponse] = []


class ScreeningResponse(BaseModel):
    """Response after candidate screening."""
    application_id: int
    eligibility: str
    llm_score: int
    reasoning: str
    bucket: Optional[str]
    constraint_results: List[ConstraintResult]
    stage_transitions: List[StageTransitionResponse]


class CandidateHistoryResponse(BaseModel):
    """Full candidate history across all roles."""
    name: str
    phone: str
    created_at: datetime
    applications: List[ApplicationResponse]


class RoleDashboardCandidate(BaseModel):
    """Candidate entry in the role dashboard."""
    application_id: int
    name: str
    phone: str
    llm_score: Optional[int]
    llm_reasoning: Optional[str]
    eligibility: Optional[str]
    current_stage: str
    bucket: Optional[str]


class RoleDashboardResponse(BaseModel):
    """Dashboard response for a role, grouped by bucket."""
    role_id: str
    role_title: str
    advance: List[RoleDashboardCandidate]
    hold: List[RoleDashboardCandidate]
    reject: List[RoleDashboardCandidate]
    pending: List[RoleDashboardCandidate]


class RoleConfigResponse(BaseModel):
    """Role configuration details."""
    role_id: str
    title: str
    required_skills: List[str]
    min_experience_years: int
    location_constraints: List[str]
    evaluation_criteria: str


class OverrideSuccessResponse(BaseModel):
    """Response after a successful bucket override."""
    message: str
    application_id: int
    old_bucket: str
    new_bucket: str
    reason: str
    overridden_by: str
    timestamp: datetime
