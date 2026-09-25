"""
Evaluation API — REST endpoints for the Independent Diagnostic Evaluator.

POST /evaluation/independent-diagnosis
POST /evaluation/compare
GET  /evaluation/{evaluation_id}
POST /evaluation/run-all-synthetic
GET  /evaluation/metrics
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.evaluation import EvaluationResult
from app.models.schemas import (
    ComparisonResult,
    EnginePrediction,
    EvaluationCaseInput,
    EvaluationMetricsReport,
    FullEvaluationResult,
    IndependentDiagnosis,
)
from app.services.evaluation.independent_evaluator import IndependentEvaluator
from app.services.evaluation.metrics import compute_metrics
from app.services.evaluation.synthetic_cases import ALL_SYNTHETIC_CASES, get_case_by_id
from pydantic import BaseModel

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


# ── Request schemas ───────────────────────────────────────────────────


class DiagnoseRequest(BaseModel):
    """Input for the independent diagnosis endpoint."""

    session_id: int | None = None
    case_id: str | None = None
    # Either provide a case_id (to load a synthetic case) or inline data.
    evaluation_input: EvaluationCaseInput | None = None


class CompareRequest(BaseModel):
    """Input for the comparison endpoint."""

    independent_diagnosis: IndependentDiagnosis
    engine_prediction: EnginePrediction


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/independent-diagnosis", response_model=IndependentDiagnosis)
def independent_diagnosis(request: DiagnoseRequest, db: Session = Depends(get_db)):
    """
    Produce an independent diagnosis from student evidence ONLY.
    The engine prediction is NOT visible.
    """
    case_input = _resolve_case_input(request)
    evaluator = IndependentEvaluator(db=db)
    return evaluator.diagnose(case_input)


@router.post("/compare", response_model=ComparisonResult)
def compare(request: CompareRequest, db: Session = Depends(get_db)):
    """
    Compare an independent diagnosis against the engine prediction.
    The engine prediction is revealed only in this call.
    """
    evaluator = IndependentEvaluator(db=db)
    return evaluator.compare(request.independent_diagnosis, request.engine_prediction)


@router.get("/{evaluation_id}", response_model=dict)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Retrieve a complete persisted evaluation result."""
    record = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.id == evaluation_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
        "evaluation_id": record.id,
        "session_id": record.session_id,
        "case_id": record.case_id,
        "independent_root_cause": record.independent_root_cause,
        "independent_specific_label": record.independent_specific_label,
        "independent_confidence": record.independent_confidence,
        "engine_root_cause": record.engine_root_cause,
        "engine_confidence": record.engine_confidence,
        "agreement": bool(record.agreement),
        "diagnostic_quality": record.diagnostic_quality,
        "observed_errors": record.observed_errors,
        "supporting_evidence": record.supporting_evidence,
        "contradicting_evidence": record.contradicting_evidence,
        "alternative_hypotheses": record.alternative_hypotheses,
        "recommended_next_question": record.recommended_next_question,
        "evaluator_reasoning_summary": record.evaluator_reasoning_summary,
        "created_at": str(record.created_at),
    }


@router.post("/run-all-synthetic", response_model=list[FullEvaluationResult])
def run_all_synthetic(db: Session = Depends(get_db)):
    """
    Run the evaluator against ALL 8 synthetic cases.
    Returns the full evaluation result for each case.
    """
    evaluator = IndependentEvaluator(db=db)
    results: list[FullEvaluationResult] = []
    for case in ALL_SYNTHETIC_CASES:
        result = evaluator.run_full_evaluation(
            case=case.evaluation_input,
            engine=case.engine_prediction,
        )
        results.append(result)
    return results


@router.get("/metrics/report", response_model=EvaluationMetricsReport)
def get_metrics(db: Session = Depends(get_db)):
    """
    Run all synthetic cases and compute aggregate metrics.
    """
    evaluator = IndependentEvaluator(db=db)
    results: list[FullEvaluationResult] = []
    for case in ALL_SYNTHETIC_CASES:
        result = evaluator.run_full_evaluation(
            case=case.evaluation_input,
            engine=case.engine_prediction,
        )
        results.append(result)
    return compute_metrics(results, ALL_SYNTHETIC_CASES)


# ── Helpers ───────────────────────────────────────────────────────────


def _resolve_case_input(request: DiagnoseRequest) -> EvaluationCaseInput:
    """Resolve the evaluation input from either a case_id or inline data."""
    if request.case_id:
        case = get_case_by_id(request.case_id)
        if not case:
            raise HTTPException(
                status_code=404, detail=f"Synthetic case '{request.case_id}' not found"
            )
        return case.evaluation_input

    if request.evaluation_input:
        return request.evaluation_input

    raise HTTPException(
        status_code=400,
        detail="Provide either case_id or evaluation_input",
    )
