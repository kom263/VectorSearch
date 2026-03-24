"""SQLAlchemy ORM models for the hiring pipeline."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Candidate(Base):
    """Candidate identified uniquely by phone number."""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate(name={self.name}, phone={self.phone})>"


class Application(Base):
    """An application by a candidate for a specific role."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    role_id = Column(String(100), nullable=False, index=True)

    # Candidate submission data
    skills = Column(JSON, nullable=False)
    years_experience = Column(Integer, nullable=False)
    location = Column(String(255), nullable=False)
    pitch = Column(Text, nullable=False)

    # Pipeline state
    current_stage = Column(String(50), nullable=False, default="intake")
    bucket = Column(String(50), nullable=True)  # advance / hold / reject

    # LLM evaluation results
    llm_score = Column(Integer, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    constraint_results = Column(JSON, nullable=True)
    eligibility = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="applications")
    stage_transitions = relationship("StageTransition", back_populates="application", cascade="all, delete-orphan")
    bucket_overrides = relationship("BucketOverride", back_populates="application", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Application(candidate_id={self.candidate_id}, role={self.role_id}, stage={self.current_stage})>"


class StageTransition(Base):
    """Audit log entry for each pipeline stage transition."""
    __tablename__ = "stage_transitions"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    from_stage = Column(String(50), nullable=True)  # null for initial entry
    to_stage = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    triggered_by = Column(String(50), nullable=False, default="system")
    timestamp = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="stage_transitions")

    def __repr__(self):
        return f"<StageTransition({self.from_stage} -> {self.to_stage})>"


class BucketOverride(Base):
    """Audit log entry when a recruiter manually overrides a bucket decision."""
    __tablename__ = "bucket_overrides"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    old_bucket = Column(String(50), nullable=False)
    new_bucket = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    overridden_by = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="bucket_overrides")

    def __repr__(self):
        return f"<BucketOverride({self.old_bucket} -> {self.new_bucket})>"
