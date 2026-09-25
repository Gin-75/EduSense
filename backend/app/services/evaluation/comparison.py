"""
Comparison Service — compare independent diagnosis vs engine prediction.

This module is invoked ONLY AFTER the independent diagnosis has been
produced.  It never feeds back into the independent evaluator.
"""

from __future__ import annotations

from app.models.schemas import (
    ComparisonResult,
    EnginePrediction,
    IndependentDiagnosis,
)
from app.services.evaluation.taxonomy import DiagnosticQuality, RootCauseCategory


def compare_diagnoses(
    independent: IndependentDiagnosis,
    engine: EnginePrediction,
) -> ComparisonResult:
    """
    Produce a structured comparison between the evaluator's independent
    diagnosis and the engine's prediction.
    """
    # ── Agreement check ──
    # Normalise both labels to uppercase for comparison.
    ind_label = independent.independent_root_cause.value.upper()
    eng_label = engine.root_cause.upper()
    agreement = ind_label == eng_label

    # ── Diagnostic quality rating ──
    quality = _rate_quality(independent, engine, agreement)

    # ── Confidence support ──
    # The engine's confidence is "supported" if the evaluator also has
    # high confidence in the same diagnosis.
    engine_conf_supported = (
        agreement
        and independent.confidence >= 0.4
        and engine.confidence <= independent.confidence + 0.25
    )

    # ── Major issue identification ──
    major_issue = _identify_major_issue(independent, engine, agreement, quality)

    # ── Recommendation ──
    recommendation = _generate_recommendation(quality, independent, engine)

    return ComparisonResult(
        engine_root_cause=engine.root_cause,
        engine_confidence=engine.confidence,
        independent_root_cause=independent.independent_root_cause.value,
        independent_confidence=independent.confidence,
        agreement=agreement,
        diagnostic_quality=quality,
        engine_confidence_supported=engine_conf_supported,
        major_issue=major_issue,
        recommendation=recommendation,
    )


# ── Internal helpers ──────────────────────────────────────────────────


def _rate_quality(
    independent: IndependentDiagnosis,
    engine: EnginePrediction,
    agreement: bool,
) -> DiagnosticQuality:
    """
    Rate the engine's diagnostic quality based on evidence alignment.
    """
    if independent.independent_root_cause == RootCauseCategory.INSUFFICIENT_EVIDENCE:
        if engine.confidence > 0.5:
            # Engine is confident but evidence is insufficient → overclaiming
            return DiagnosticQuality.UNSUPPORTED
        return DiagnosticQuality.INSUFFICIENT_EVIDENCE

    if agreement:
        if independent.confidence >= 0.4:
            return DiagnosticQuality.SUPPORTED
        return DiagnosticQuality.PARTIALLY_SUPPORTED

    # Disagreement — check if the engine's cause appears in the evaluator's
    # hypothesis list (even if not top-ranked).
    engine_in_top_3 = any(
        h.cause.value.upper() == engine.root_cause.upper()
        for h in independent.hypotheses[:3]
    )
    if engine_in_top_3:
        return DiagnosticQuality.PARTIALLY_SUPPORTED

    return DiagnosticQuality.UNSUPPORTED


def _identify_major_issue(
    independent: IndependentDiagnosis,
    engine: EnginePrediction,
    agreement: bool,
    quality: DiagnosticQuality,
) -> str:
    if quality == DiagnosticQuality.SUPPORTED:
        return ""

    if (
        independent.independent_root_cause == RootCauseCategory.INSUFFICIENT_EVIDENCE
        and engine.confidence > 0.5
    ):
        return (
            "Engine reports high confidence but available evidence is "
            "insufficient to reliably distinguish between competing causes. "
            "The engine may be overconfident."
        )

    if not agreement:
        return (
            f"Disagreement: evaluator concluded {independent.independent_root_cause.value} "
            f"(conf {independent.confidence:.2f}) while engine predicted "
            f"{engine.root_cause} (conf {engine.confidence:.2f}). "
            "The observed error pattern is more consistent with the evaluator's diagnosis."
        )

    if quality == DiagnosticQuality.PARTIALLY_SUPPORTED:
        return (
            "The engine's diagnosis is plausible but not strongly supported. "
            "More diagnostic questions are needed."
        )

    return ""


def _generate_recommendation(
    quality: DiagnosticQuality,
    independent: IndependentDiagnosis,
    engine: EnginePrediction,
) -> str:
    if quality == DiagnosticQuality.SUPPORTED:
        return "No action needed — diagnosis is well supported."

    if quality == DiagnosticQuality.UNSUPPORTED:
        return (
            f"Revise the diagnostic logic. The engine diagnosed "
            f"'{engine.root_cause}' but the evidence better supports "
            f"'{independent.independent_root_cause.value}'. "
            f"Recommended next step: {independent.most_informative_next_question}"
        )

    if quality == DiagnosticQuality.PARTIALLY_SUPPORTED:
        return (
            f"Gather more evidence before finalising the diagnosis. "
            f"Recommended next step: {independent.most_informative_next_question}"
        )

    # INSUFFICIENT_EVIDENCE
    return (
        "Collect more student responses before attempting a diagnosis. "
        f"Recommended next step: {independent.most_informative_next_question}"
    )
