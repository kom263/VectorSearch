"""Recruiter dashboard API endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    RoleDashboardResponse, RoleDashboardCandidate,
    CandidateHistoryResponse, ApplicationResponse,
    StageTransitionResponse, BucketOverrideResponse,
    BucketOverrideRequest, OverrideSuccessResponse, ConstraintResult
)
from app.models import Candidate, Application, StageTransition, BucketOverride
from app.services.role_config import get_role_config

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/role/{role_id}", response_model=RoleDashboardResponse)
def get_role_dashboard(role_id: str, db: Session = Depends(get_db)):
    """
    Get all candidates for a role, grouped by bucket (Advance / Hold / Reject).
    Shows scores and LLM reasoning.
    """
    config = get_role_config(role_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")

    applications = db.query(Application).filter(Application.role_id == role_id).all()

    advance, hold, reject, pending = [], [], [], []
    for app in applications:
        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()
        entry = RoleDashboardCandidate(
            application_id=app.id,
            name=candidate.name if candidate else "Unknown",
            phone=candidate.phone if candidate else "",
            llm_score=app.llm_score,
            llm_reasoning=app.llm_reasoning,
            eligibility=app.eligibility,
            current_stage=app.current_stage,
            bucket=app.bucket
        )
        if app.bucket == "advance":
            advance.append(entry)
        elif app.bucket == "hold":
            hold.append(entry)
        elif app.bucket == "reject":
            reject.append(entry)
        else:
            pending.append(entry)

    return RoleDashboardResponse(
        role_id=role_id,
        role_title=config["title"],
        advance=advance,
        hold=hold,
        reject=reject,
        pending=pending
    )


@router.get("/candidate/{phone}", response_model=CandidateHistoryResponse)
def get_candidate_history(phone: str, db: Session = Depends(get_db)):
    """
    Get a candidate's full history across all roles,
    stage transitions, and scores.
    """
    candidate = db.query(Candidate).filter(Candidate.phone == phone).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"No candidate found with phone: {phone}")

    applications = []
    for app in candidate.applications:
        transitions = [
            StageTransitionResponse(
                from_stage=t.from_stage,
                to_stage=t.to_stage,
                reason=t.reason,
                triggered_by=t.triggered_by,
                timestamp=t.timestamp
            )
            for t in app.stage_transitions
        ]
        overrides = [
            BucketOverrideResponse(
                old_bucket=o.old_bucket,
                new_bucket=o.new_bucket,
                reason=o.reason,
                overridden_by=o.overridden_by,
                timestamp=o.timestamp
            )
            for o in app.bucket_overrides
        ]
        constraint_results = [
            ConstraintResult(**c) for c in (app.constraint_results or [])
        ]
        applications.append(ApplicationResponse(
            id=app.id,
            role_id=app.role_id,
            candidate_name=candidate.name,
            candidate_phone=candidate.phone,
            skills=app.skills,
            years_experience=app.years_experience,
            location=app.location,
            pitch=app.pitch,
            current_stage=app.current_stage,
            bucket=app.bucket,
            llm_score=app.llm_score,
            llm_reasoning=app.llm_reasoning,
            constraint_results=constraint_results,
            eligibility=app.eligibility,
            created_at=app.created_at,
            updated_at=app.updated_at,
            stage_transitions=transitions,
            bucket_overrides=overrides
        ))

    return CandidateHistoryResponse(
        name=candidate.name,
        phone=candidate.phone,
        created_at=candidate.created_at,
        applications=applications
    )


@router.post("/override", response_model=OverrideSuccessResponse)
def override_bucket(request: BucketOverrideRequest, db: Session = Depends(get_db)):
    """
    Manually override a candidate's bucket decision.
    The override is logged in the audit trail.
    """
    application = db.query(Application).filter(Application.id == request.application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail=f"Application {request.application_id} not found")

    if not application.bucket:
        raise HTTPException(status_code=400, detail="Cannot override: application has not been bucketed yet")

    old_bucket = application.bucket
    if old_bucket == request.new_bucket:
        raise HTTPException(status_code=400, detail=f"Application is already in '{old_bucket}' bucket")

    # Create override record
    override = BucketOverride(
        application_id=application.id,
        old_bucket=old_bucket,
        new_bucket=request.new_bucket,
        reason=request.reason,
        overridden_by=request.overridden_by,
        timestamp=datetime.utcnow()
    )
    db.add(override)

    # Log the transition
    transition = StageTransition(
        application_id=application.id,
        from_stage=application.current_stage,
        to_stage=application.current_stage,
        reason=f"Recruiter override: {old_bucket} → {request.new_bucket}. Reason: {request.reason}",
        triggered_by=request.overridden_by,
        timestamp=datetime.utcnow()
    )
    db.add(transition)

    # Update the bucket
    application.bucket = request.new_bucket
    application.updated_at = datetime.utcnow()

    db.commit()

    return OverrideSuccessResponse(
        message="Bucket override successful",
        application_id=application.id,
        old_bucket=old_bucket,
        new_bucket=request.new_bucket,
        reason=request.reason,
        overridden_by=request.overridden_by,
        timestamp=override.timestamp
    )
