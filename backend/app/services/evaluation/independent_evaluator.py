"""
Independent Evaluator — orchestrator service.

This is the public API of the evaluation subsystem.  It coordinates:
    1.  Rule-based independent diagnosis  (evidence_analyzer)
    2.  Optional LLM-based independent diagnosis  (llm_provider)
    3.  Comparison against the engine prediction  (comparison)
    4.  Persistence of the result  (evaluation model)

The evaluator is READ-ONLY with respect to all engine tables.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationResult
from app.models.schemas import (
    ComparisonResult,
    EnginePrediction,
    EvaluationCaseInput,
    FullEvaluationResult,
    IndependentDiagnosis,
)
from app.services.evaluation.comparison import compare_diagnoses
from app.services.evaluation.evidence_analyzer import produce_independent_diagnosis
from app.services.evaluation.llm_provider import DiagnosticEvaluatorProvider


class IndependentEvaluator:
    """
    Facade that runs a full evaluation pipeline.

    Parameters
    ----------
    db : Session
        Read-only handle for persisting evaluation results.
    llm_provider : DiagnosticEvaluatorProvider, optional
        If supplied, the evaluator will attempt the LLM path first and
        fall back to the rule-based path on failure.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        llm_provider: Optional[DiagnosticEvaluatorProvider] = None,
    ):
        self._db = db
        self._llm = llm_provider

    # ── Step 1: Independent diagnosis ─────────────────────────────────

    def diagnose(self, case: EvaluationCaseInput) -> IndependentDiagnosis:
        """
        Produce an independent diagnosis from student evidence ONLY.
        No engine prediction is visible at this point.
        """
        # MVP: always use rule-based.  When an LLM is configured and
        # the async path is called, we try the LLM first.
        return produce_independent_diagnosis(case)

    async def diagnose_async(self, case: EvaluationCaseInput) -> IndependentDiagnosis:
        """Async variant — tries LLM first, falls back to rules."""
        if self._llm is not None:
            try:
                return await self._llm.independent_diagnose(case)
            except (NotImplementedError, Exception):
                pass
        return produce_independent_diagnosis(case)

    # ── Step 2: Comparison (engine prediction revealed) ───────────────

    def compare(
        self,
        independent: IndependentDiagnosis,
        engine: EnginePrediction,
    ) -> ComparisonResult:
        """Compare the independent diagnosis with the engine prediction."""
        return compare_diagnoses(independent, engine)

    async def compare_async(
        self,
        independent: IndependentDiagnosis,
        engine: EnginePrediction,
    ) -> ComparisonResult:
        """Async variant — tries LLM comparison, falls back to rules."""
        if self._llm is not None:
            try:
                return await self._llm.compare(independent, engine)
            except (NotImplementedError, Exception):
                pass
        return compare_diagnoses(independent, engine)

    # ── Full pipeline ─────────────────────────────────────────────────

    def run_full_evaluation(
        self,
        case: EvaluationCaseInput,
        engine: EnginePrediction,
    ) -> FullEvaluationResult:
        """
        Run the complete evaluation pipeline synchronously:
            diagnose → compare → persist.
        """
        independent = self.diagnose(case)
        comparison = self.compare(independent, engine)
        result = FullEvaluationResult(
            session_id=case.session_id,
            case_id=case.case_id,
            independent_diagnosis=independent,
            comparison=comparison,
        )

        # Persist if we have a DB session
        if self._db is not None:
            self._persist(result)

        return result

    # ── Persistence (append-only) ─────────────────────────────────────

    def _persist(self, result: FullEvaluationResult) -> int:
        """
        Write the evaluation result to the evaluation_results table.
        This NEVER touches engine tables.
        """
        diag = result.independent_diagnosis
        comp = result.comparison

        record = EvaluationResult(
            session_id=result.session_id,
            case_id=result.case_id,
            independent_root_cause=diag.independent_root_cause.value,
            independent_specific_label=diag.specific_label,
            independent_confidence=diag.confidence,
            engine_root_cause=comp.engine_root_cause if comp else None,
            engine_confidence=comp.engine_confidence if comp else None,
            agreement=1 if (comp and comp.agreement) else 0,
            diagnostic_quality=comp.diagnostic_quality.value if comp else None,
            observed_errors=[diag.observed_error],
            supporting_evidence=diag.evidence_summary,
            contradicting_evidence=(
                [e for h in diag.hypotheses for e in h.contradicting_evidence]
            ),
            alternative_hypotheses=[
                {
                    "cause": h.cause.value,
                    "confidence": h.confidence,
                    "specific_label": h.specific_label,
                }
                for h in diag.hypotheses[1:]  # skip the top hypothesis
            ],
            recommended_next_question=diag.most_informative_next_question,
            evaluator_reasoning_summary={
                "error_features": diag.error_features.model_dump() if diag.error_features else None,
                "top_hypothesis": diag.hypotheses[0].model_dump() if diag.hypotheses else None,
            },
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        result.evaluation_id = record.id
        return record.id
