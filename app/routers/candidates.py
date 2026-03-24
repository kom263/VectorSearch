"""Candidate application API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    CandidateApplyRequest, ScreeningResponse,
    CandidateHistoryResponse, ApplicationResponse,
    StageTransitionResponse, BucketOverrideResponse, ConstraintResult
)
from app.models import Candidate, Application
from app.services.pipeline_engine import process_application

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


@router.post("/apply", response_model=ScreeningResponse)
def apply_for_role(request: CandidateApplyRequest, db: Session = Depends(get_db)):
    """
    Submit a candidate application for a specific role.
    Triggers the full 3-stage pipeline: Intake → AI Screen → Decision Bucket.
    """
    try:
        application, constraint_results = process_application(db, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

    transitions = [
        StageTransitionResponse(
            from_stage=t.from_stage,
            to_stage=t.to_stage,
            reason=t.reason,
            triggered_by=t.triggered_by,
            timestamp=t.timestamp
        )
        for t in application.stage_transitions
    ]

    constraints = [
        ConstraintResult(**c) for c in (constraint_results or [])
    ]

    return ScreeningResponse(
        application_id=application.id,
        eligibility=application.eligibility or "Unknown",
        llm_score=application.llm_score or 0,
        reasoning=application.llm_reasoning or "",
        bucket=application.bucket,
        constraint_results=constraints,
        stage_transitions=transitions
    )


@router.get("/{phone}/status", response_model=CandidateHistoryResponse)
def get_candidate_status(phone: str, db: Session = Depends(get_db)):
    """
    Get a candidate's full history across all roles, including
    stage transitions and scores.
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
