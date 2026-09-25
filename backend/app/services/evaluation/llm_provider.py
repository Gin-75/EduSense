"""
LLM Provider — abstract interface for LLM-based evaluation.

The evaluator's core logic is rule-based for the MVP, but production
evaluation will delegate to an LLM.  This module defines an abstract
interface so that the concrete provider (Claude, Gemini, OpenAI, local)
can be swapped via dependency injection without touching the evaluator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.schemas import (
    ComparisonResult,
    EnginePrediction,
    EvaluationCaseInput,
    IndependentDiagnosis,
)


class DiagnosticEvaluatorProvider(ABC):
    """
    Abstract LLM provider that the IndependentEvaluator can delegate to.

    Implementations MUST follow the two-call architecture to prevent
    information leakage:

        CALL 1  — independent_diagnose(case)
                   The engine prediction is NOT available.
        CALL 2  — compare(independent_diagnosis, engine_prediction)
                   The engine prediction is revealed only here.
    """

    @abstractmethod
    async def independent_diagnose(
        self, case: EvaluationCaseInput
    ) -> IndependentDiagnosis:
        """
        Produce an independent diagnosis from student evidence ONLY.
        The engine prediction MUST NOT be visible to this call.
        """
        ...

    @abstractmethod
    async def compare(
        self,
        independent: IndependentDiagnosis,
        engine: EnginePrediction,
    ) -> ComparisonResult:
        """
        Compare the independent diagnosis against the engine prediction.
        """
        ...


class StubLLMProvider(DiagnosticEvaluatorProvider):
    """
    No-op provider that returns None sentinels.
    Used in tests or when no LLM API key is configured.
    """

    async def independent_diagnose(
        self, case: EvaluationCaseInput
    ) -> IndependentDiagnosis:
        # Fall through — the orchestrator will use the rule-based path
        raise NotImplementedError("Stub provider — use the rule-based evaluator")

    async def compare(
        self,
        independent: IndependentDiagnosis,
        engine: EnginePrediction,
    ) -> ComparisonResult:
        raise NotImplementedError("Stub provider — use the rule-based comparison")
