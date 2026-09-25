"""
Pydantic schemas for the Independent Diagnostic Evaluator.

These schemas define the structured data that flows through the
evaluation pipeline.  They are completely separate from the Diagnostic
Engine's own schemas/models — the evaluator is read-only with respect
to the engine state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.services.evaluation.taxonomy import DiagnosticQuality, RootCauseCategory


# ── Inputs ────────────────────────────────────────────────────────────


class StudentResponseRecord(BaseModel):
    """One student attempt on a single question."""

    question_id: int
    question_content: str
    expected_answer: str
    student_answer: str
    is_correct: bool
    error_signature: Optional[str] = None
    student_work_steps: Optional[list[str]] = None
    skill_ids: list[int] = Field(default_factory=list)
    skill_names: list[str] = Field(default_factory=list)


class SkillRecord(BaseModel):
    id: int
    name: str
    subject: str
    difficulty: float = 0.5


class MisconceptionRecord(BaseModel):
    id: int
    description: str
    related_skill_id: int
    related_skill_name: str = ""


class DiagnosticQuestionRecord(BaseModel):
    """A diagnostic question that was asked during the session."""

    question_id: int
    question_content: str
    purpose: str = ""  # why this question was selected
    student_answer: str = ""
    is_correct: bool = False
    error_signature: Optional[str] = None


class EvaluationCaseInput(BaseModel):
    """
    Everything the evaluator needs to produce an independent diagnosis.
    This is the single entry-point DTO.
    """

    session_id: Optional[int] = None
    case_id: Optional[str] = None  # for synthetic cases
    student_responses: list[StudentResponseRecord]
    student_work: Optional[list[str]] = None
    error_signatures: list[str] = Field(default_factory=list)
    available_skills: list[SkillRecord] = Field(default_factory=list)
    available_misconceptions: list[MisconceptionRecord] = Field(default_factory=list)
    diagnostic_history: list[DiagnosticQuestionRecord] = Field(default_factory=list)


# ── Evidence Analysis ─────────────────────────────────────────────────


class ErrorFeatures(BaseModel):
    """Statistical / structural features extracted from student errors."""

    total_attempts: int = 0
    correct_count: int = 0
    error_count: int = 0
    unique_error_signatures: int = 0
    most_common_error: Optional[str] = None
    most_common_error_count: int = 0
    repetition_ratio: float = 0.0  # max_repetition / error_count
    skills_with_errors: list[str] = Field(default_factory=list)
    skill_error_count: int = 0  # distinct skills that have errors
    has_work_steps: bool = False
    error_in_first_step: bool = False
    error_in_last_step_only: bool = False
    errors_structurally_similar: bool = False


class HypothesisDetail(BaseModel):
    """A single candidate explanation for the student's error."""

    cause: RootCauseCategory
    specific_label: Optional[str] = None  # e.g. "incomplete_distribution"
    confidence: float = 0.0
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    evidence_strength: float = 0.0  # 0‒1


# ── Outputs ───────────────────────────────────────────────────────────


class IndependentDiagnosis(BaseModel):
    """Result of the evaluator's independent diagnostic reasoning."""

    observed_error: str
    skill_involved: str
    hypotheses: list[HypothesisDetail]
    independent_root_cause: RootCauseCategory
    specific_label: Optional[str] = None
    confidence: float = 0.0
    evidence_summary: list[str] = Field(default_factory=list)
    most_informative_next_question: str = ""
    error_features: Optional[ErrorFeatures] = None


class ComparisonResult(BaseModel):
    """Comparison of independent diagnosis vs engine diagnosis."""

    engine_root_cause: str
    engine_confidence: float = 0.0
    independent_root_cause: str
    independent_confidence: float = 0.0
    agreement: bool = False
    diagnostic_quality: DiagnosticQuality = DiagnosticQuality.INSUFFICIENT_EVIDENCE
    engine_confidence_supported: bool = False
    major_issue: str = ""
    recommendation: str = ""


class FullEvaluationResult(BaseModel):
    """Complete structured output of an evaluation run."""

    evaluation_id: Optional[int] = None
    session_id: Optional[int] = None
    case_id: Optional[str] = None
    independent_diagnosis: IndependentDiagnosis
    comparison: Optional[ComparisonResult] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Engine prediction (supplied separately to prevent leakage) ────────


class EnginePrediction(BaseModel):
    """The Diagnostic Engine's prediction, supplied ONLY in the comparison stage."""

    root_cause: str
    confidence: float = 0.0
    hypotheses: Optional[dict] = None  # engine's raw hypothesis dict
    diagnosis_detail: Optional[str] = None


# ── Metrics ───────────────────────────────────────────────────────────


class SyntheticCaseDefinition(BaseModel):
    """A synthetic evaluation scenario with a known ground-truth root cause."""

    case_id: str
    description: str
    evaluation_input: EvaluationCaseInput
    engine_prediction: EnginePrediction
    ground_truth_root_cause: RootCauseCategory
    ground_truth_specific_label: Optional[str] = None


class EvaluationMetricsReport(BaseModel):
    """Aggregate metrics computed over a set of evaluation runs."""

    total_cases: int = 0
    root_cause_accuracy: float = 0.0
    top_2_accuracy: float = 0.0
    agreement_rate: float = 0.0
    false_diagnosis_rate: float = 0.0
    insufficient_evidence_rate: float = 0.0
    average_confidence: float = 0.0
    confidence_when_correct: float = 0.0
    confidence_when_wrong: float = 0.0
    average_questions_to_diagnosis: float = 0.0
    per_case: list[dict] = Field(default_factory=list)

# ── Simulation ────────────────────────────────────────────────────────

class SimulationResult(BaseModel):
    """Result of an end-to-end student simulation."""
    student_id: str
    archetype: str
    ground_truth: dict # Dump of GroundTruth
    engine_diagnosis: str
    engine_confidence: float
    correct: bool
    questions_used: int
    false_diagnosis: bool = False
    insufficient_evidence: bool = False
    questions_asked: list[str] = []
    student_responses: list[str] = []
    detected_errors: list[str] = []
    engine_hypotheses: dict = {}
    failure_reason: Optional[str] = None
