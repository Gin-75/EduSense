"""
SQLAlchemy model for persisted evaluation results.

The EvaluationResult table is append-only with respect to the
Diagnostic Engine — the evaluator NEVER modifies StudentSkillState,
DiagnosticSession, or any engine table.
"""

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func

from app.database import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=True, index=True)
    case_id = Column(String, nullable=True, index=True)  # for synthetic cases

    # Independent evaluator outputs
    independent_root_cause = Column(String, nullable=False)
    independent_specific_label = Column(String, nullable=True)
    independent_confidence = Column(Float, default=0.0)

    # Engine outputs (stored for comparison only)
    engine_root_cause = Column(String, nullable=True)
    engine_confidence = Column(Float, nullable=True)

    # Comparison
    agreement = Column(Integer, default=0)  # 0 = disagree, 1 = agree
    diagnostic_quality = Column(String, nullable=True)

    # Structured evidence (JSON)
    observed_errors = Column(JSON, nullable=True)
    supporting_evidence = Column(JSON, nullable=True)
    contradicting_evidence = Column(JSON, nullable=True)
    alternative_hypotheses = Column(JSON, nullable=True)
    recommended_next_question = Column(Text, nullable=True)
    evaluator_reasoning_summary = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
