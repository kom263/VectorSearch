"""Pipeline engine: 3-stage state machine for candidate processing.

Stages:
1. Intake — Validate, create/find candidate, de-duplicate by phone+role
2. AI Screen — LLM evaluation runs automatically; ineligible candidates rejected
3. Decision Bucket — Score-based bucketing (Advance ≥80, Hold 50-79, Reject <50)

Every stage transition is logged with timestamp and reason for full audit trail.
"""

import logging
from datetime import datetime
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from app.models import Candidate, Application, StageTransition
from app.services.llm_service import evaluate_candidate
from app.services.role_config import get_role_config

logger = logging.getLogger(__name__)


def _log_transition(db: Session, application: Application,
                    from_stage: str | None, to_stage: str,
                    reason: str, triggered_by: str = "system"):
    """Log a stage transition in the audit trail."""
    transition = StageTransition(
        application_id=application.id,
        from_stage=from_stage,
        to_stage=to_stage,
        reason=reason,
        triggered_by=triggered_by,
        timestamp=datetime.utcnow()
    )
    db.add(transition)
    application.current_stage = to_stage
    application.updated_at = datetime.utcnow()
    
    logger.info(
        "Application %d: %s → %s (%s)",
        application.id, from_stage or "START", to_stage, reason[:80]
    )


def _check_constraints(candidate_data: Dict, role_config: Dict) -> List[Dict]:
    """Check hard constraints (skills, experience, location) before LLM evaluation."""
    results = []

    # Skills check
    required = set(s.lower() for s in role_config["required_skills"])
    candidate = set(s.lower() for s in candidate_data["skills"])
    matched = required & candidate
    skills_pass = len(matched) >= 1  # At least 1 required skill
    results.append({
        "constraint": "skills_match",
        "passed": skills_pass,
        "detail": f"Matched {len(matched)}/{len(required)} required skills: {', '.join(matched) if matched else 'none'}"
    })

    # Experience check
    min_exp = role_config["min_experience_years"]
    exp_pass = candidate_data["years_experience"] >= min_exp
    results.append({
        "constraint": "minimum_experience",
        "passed": exp_pass,
        "detail": f"Candidate has {candidate_data['years_experience']} years, minimum is {min_exp}"
    })

    # Location check
    allowed = [loc.lower() for loc in role_config["location_constraints"]]
    loc = candidate_data["location"].lower()
    loc_pass = any(a in loc or loc in a for a in allowed) or "remote" in allowed
    results.append({
        "constraint": "location",
        "passed": loc_pass,
        "detail": f"Candidate location '{candidate_data['location']}' vs allowed: {', '.join(role_config['location_constraints'])}"
    })

    logger.info(
        "Constraint check results: skills=%s, experience=%s, location=%s",
        "PASS" if skills_pass else "FAIL",
        "PASS" if exp_pass else "FAIL",
        "PASS" if loc_pass else "FAIL"
    )

    return results


def process_application(db: Session, candidate_data: Dict) -> Tuple[Application, List[Dict]]:
    """
    Process a candidate application through the 3-stage pipeline.
    
    Stage 1 - Intake: Validate, create/find candidate, de-duplicate
    Stage 2 - AI Screen: LLM evaluation
    Stage 3 - Decision Bucket: Score-based bucketing
    
    Returns:
        Tuple of (Application, constraint_results)
    
    Raises:
        ValueError: If role not found or duplicate application
    """
    role_id = candidate_data["role_id"]
    role_config = get_role_config(role_id)
    if not role_config:
        raise ValueError(f"Role '{role_id}' not found")

    logger.info(
        "Processing application: candidate='%s', phone='%s', role='%s'",
        candidate_data["name"], candidate_data["phone"], role_id
    )

    # ── Stage 1: Intake ──────────────────────────────────────────

    # Find or create candidate by phone
    candidate = db.query(Candidate).filter(Candidate.phone == candidate_data["phone"]).first()
    if not candidate:
        candidate = Candidate(
            name=candidate_data["name"],
            phone=candidate_data["phone"]
        )
        db.add(candidate)
        db.flush()  # Get the ID
        logger.info("Created new candidate record: id=%d, phone=%s", candidate.id, candidate.phone)
    else:
        # Update name if different
        candidate.name = candidate_data["name"]
        logger.info("Found existing candidate: id=%d, phone=%s", candidate.id, candidate.phone)

    # Check for duplicate application (same phone + same role)
    existing = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.role_id == role_id
    ).first()
    if existing:
        logger.warning(
            "Duplicate application rejected: phone=%s, role=%s, existing_id=%d",
            candidate_data["phone"], role_id, existing.id
        )
        raise ValueError(
            f"Candidate with phone '{candidate_data['phone']}' has already applied for role '{role_id}'. "
            f"Application ID: {existing.id}, Current stage: {existing.current_stage}"
        )

    # Create application record
    application = Application(
        candidate_id=candidate.id,
        role_id=role_id,
        skills=candidate_data["skills"],
        years_experience=candidate_data["years_experience"],
        location=candidate_data["location"],
        pitch=candidate_data["pitch"],
        current_stage="intake"
    )
    db.add(application)
    db.flush()

    _log_transition(db, application, None, "intake",
                    "Candidate record created and validated")

    # Check hard constraints
    constraint_results = _check_constraints(candidate_data, role_config)
    application.constraint_results = constraint_results

    # ── Stage 2: AI Screen ───────────────────────────────────────

    _log_transition(db, application, "intake", "ai_screen",
                    "Advancing to AI screening evaluation")

    # Run LLM evaluation
    llm_result = evaluate_candidate(candidate_data, role_config)
    application.llm_score = llm_result["score"]
    application.llm_reasoning = llm_result["reasoning"]
    application.eligibility = llm_result["eligibility"]

    logger.info(
        "LLM result for application %d: score=%d, eligibility=%s",
        application.id, llm_result["score"], llm_result["eligibility"]
    )

    if llm_result["eligibility"] == "Ineligible":
        # Reject with reason
        application.bucket = "reject"
        _log_transition(db, application, "ai_screen", "decision_bucket",
                        f"Rejected: LLM score {llm_result['score']}/100. {llm_result['reasoning']}")
    else:
        # ── Stage 3: Decision Bucket ─────────────────────────────
        _log_transition(db, application, "ai_screen", "decision_bucket",
                        f"Eligible: LLM score {llm_result['score']}/100. Advancing to decision bucket.")

        score = llm_result["score"]
        if score >= 80:
            application.bucket = "advance"
            _log_transition(db, application, "decision_bucket", "completed",
                            f"Score {score} >= 80: Strong fit. Advancing to interview.")
        elif score >= 50:
            application.bucket = "hold"
            _log_transition(db, application, "decision_bucket", "completed",
                            f"Score {score} (50-79): Moderate fit. Surfaced for recruiter review.")
        else:
            # This shouldn't normally happen since <50 is Ineligible, but handle edge cases
            application.bucket = "reject"
            alternate_roles = role_config.get("alternate_roles", [])
            alt_msg = f" Suggested alternate roles: {', '.join(alternate_roles)}" if alternate_roles else ""
            _log_transition(db, application, "decision_bucket", "completed",
                            f"Score {score} < 50: Below threshold.{alt_msg}")

    logger.info(
        "Application %d completed: bucket=%s, score=%d",
        application.id, application.bucket, application.llm_score or 0
    )

    db.commit()
    db.refresh(application)
    return application, constraint_results
