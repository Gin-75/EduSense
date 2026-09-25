"""
Evidence Analyzer — Feature extraction and hypothesis scoring.

This is the analytical core of the Independent Evaluator.

CRITICAL DESIGN RULE:
    This module does NOT contain any hard-coded mapping from a specific
    error signature to a specific root cause.  Instead it:

    1.  Extracts *structural* features from the student's error history
        (repetition counts, consistency, scope, location in work steps).
    2.  Scores every root-cause category against those features using
        general statistical / pedagogical heuristics.
    3.  Optionally narrows a MISCONCEPTION diagnosis to a specific label
        by checking which known misconceptions in the database are
        associated with the affected skills.

    The heuristics answer:  "Given HOW the errors look statistically,
    which category of cause is most likely?"  They do NOT answer:
    "Error X means cause Y."
"""

from __future__ import annotations

from collections import Counter
from typing import Optional

from app.models.schemas import (
    ErrorFeatures,
    EvaluationCaseInput,
    HypothesisDetail,
    IndependentDiagnosis,
)
from app.services.evaluation.taxonomy import RootCauseCategory


# ── 1.  Feature Extraction ────────────────────────────────────────────


def extract_error_features(case: EvaluationCaseInput) -> ErrorFeatures:
    """
    Turn raw student responses into a statistical feature vector.
    No root-cause inference happens here — only measurement.
    """
    total = len(case.student_responses)
    correct = sum(1 for r in case.student_responses if r.is_correct)
    errors = total - correct

    # Count error-signature repetitions
    sig_counter: Counter[str] = Counter()
    for r in case.student_responses:
        if not r.is_correct and r.error_signature:
            sig_counter[r.error_signature] += 1

    unique_sigs = len(sig_counter)
    most_common = sig_counter.most_common(1)[0] if sig_counter else (None, 0)
    most_common_error = most_common[0]
    most_common_count = most_common[1]
    rep_ratio = most_common_count / errors if errors > 0 else 0.0

    # Which skills have errors?
    skills_with_errors: list[str] = []
    for r in case.student_responses:
        if not r.is_correct:
            skills_with_errors.extend(r.skill_names)
    skills_with_errors = list(set(skills_with_errors))

    # Work-step analysis
    has_work = any(
        r.student_work_steps and len(r.student_work_steps) > 0
        for r in case.student_responses
        if not r.is_correct
    )

    error_in_first = False
    error_in_last_only = False
    if has_work:
        for r in case.student_responses:
            if not r.is_correct and r.student_work_steps and len(r.student_work_steps) >= 2:
                # Heuristic: if the first work step already deviates, flag it.
                # We compare student's first step to the expected answer to see
                # if the error appears early (conceptual) or late (computational).
                # A more sophisticated parser could compare step-by-step, but for
                # the MVP we check whether the first recorded step already contains
                # the error_signature keyword.
                first_step = r.student_work_steps[0].lower()
                last_step = r.student_work_steps[-1].lower()
                if r.error_signature and r.error_signature.lower() in first_step:
                    error_in_first = True
                elif r.error_signature and r.error_signature.lower() in last_step:
                    error_in_last_only = True

    # Structural similarity: are the wrong answers structurally similar to
    # each other?  Simple heuristic — if >70 % of errors share the same
    # error signature, the errors are structurally similar.
    structurally_similar = rep_ratio >= 0.7 and errors >= 2

    return ErrorFeatures(
        total_attempts=total,
        correct_count=correct,
        error_count=errors,
        unique_error_signatures=unique_sigs,
        most_common_error=most_common_error,
        most_common_error_count=most_common_count,
        repetition_ratio=rep_ratio,
        skills_with_errors=skills_with_errors,
        skill_error_count=len(skills_with_errors),
        has_work_steps=has_work,
        error_in_first_step=error_in_first,
        error_in_last_step_only=error_in_last_only,
        errors_structurally_similar=structurally_similar,
    )


# ── 2.  Hypothesis Generation & Scoring ──────────────────────────────


# Thresholds (can be tuned experimentally; Section 16 of the plan)
_MIN_EVIDENCE_FOR_DIAGNOSIS = 2  # need at least 2 error observations
_STRONG_REPETITION_THRESHOLD = 0.7
_CONFIDENCE_CAP_SINGLE_ERROR = 0.45  # never be very confident from 1 error


def _score_misconception(f: ErrorFeatures) -> tuple[float, list[str], list[str]]:
    """Score evidence for/against MISCONCEPTION."""
    sup: list[str] = []
    con: list[str] = []
    score = 0.0

    if f.errors_structurally_similar:
        score += 0.35
        sup.append(
            f"Same error pattern repeated {f.most_common_error_count} times "
            f"(repetition ratio {f.repetition_ratio:.2f})"
        )
    else:
        con.append("Errors are not structurally similar across attempts")

    if f.most_common_error_count >= 3:
        score += 0.15
        sup.append(f"Error repeated ≥3 times ({f.most_common_error_count})")

    if f.most_common_error_count >= 2 and f.unique_error_signatures == 1:
        score += 0.10
        sup.append("Only one distinct error pattern observed — consistent")

    if f.error_in_first_step:
        score += 0.05
        sup.append("Error appears in the first transformation step")

    if f.error_count == 1:
        con.append("Only one error observed — could be careless")
        score -= 0.10

    if f.correct_count > 0 and f.error_count == 1:
        con.append("Student answered other questions correctly")
        score -= 0.05

    return max(score, 0.0), sup, con


def _score_careless(f: ErrorFeatures) -> tuple[float, list[str], list[str]]:
    """Score evidence for/against CARELESS_ERROR."""
    sup: list[str] = []
    con: list[str] = []
    score = 0.0

    if f.error_count == 1 and f.correct_count >= 1:
        score += 0.35
        sup.append("Single error among otherwise correct responses")

    if f.error_count == 1 and f.total_attempts >= 3:
        score += 0.10
        sup.append(f"1 error out of {f.total_attempts} attempts")

    if f.errors_structurally_similar:
        con.append("Repeated structurally similar errors — not careless")
        score -= 0.25

    if f.most_common_error_count >= 2:
        con.append(f"Same error occurred {f.most_common_error_count} times")
        score -= 0.15

    return max(score, 0.0), sup, con


def _score_computational(f: ErrorFeatures) -> tuple[float, list[str], list[str]]:
    """Score evidence for/against COMPUTATIONAL_ERROR."""
    sup: list[str] = []
    con: list[str] = []
    score = 0.0

    if f.error_in_last_step_only:
        score += 0.30
        sup.append("Error appears only in the final computation step")

    if f.unique_error_signatures > 1 and not f.errors_structurally_similar:
        score += 0.10
        sup.append("Multiple distinct error signatures — varied mistakes")

    if f.errors_structurally_similar:
        con.append("Errors are structurally consistent — unlikely pure arithmetic slip")
        score -= 0.15

    if f.error_in_first_step:
        con.append("Error is in the first step — not a late computation issue")
        score -= 0.10

    return max(score, 0.0), sup, con


def _score_procedural_gap(f: ErrorFeatures) -> tuple[float, list[str], list[str]]:
    """Score evidence for/against PROCEDURAL_GAP."""
    sup: list[str] = []
    con: list[str] = []
    score = 0.0

    if f.unique_error_signatures >= 2 and not f.errors_structurally_similar:
        score += 0.25
        sup.append("Multiple different error types — may not know procedure")

    if f.skill_error_count > 1:
        score += 0.10
        sup.append(f"Errors span {f.skill_error_count} distinct skills")

    if f.errors_structurally_similar and f.unique_error_signatures == 1:
        con.append("One consistent error pattern — more specific than a procedural gap")
        score -= 0.10

    return max(score, 0.0), sup, con


def _score_conceptual_gap(f: ErrorFeatures) -> tuple[float, list[str], list[str]]:
    """Score evidence for/against CONCEPTUAL_GAP."""
    sup: list[str] = []
    con: list[str] = []
    score = 0.0

    if f.skill_error_count > 1:
        score += 0.20
        sup.append(f"Errors span {f.skill_error_count} distinct skills")

    if f.error_in_first_step:
        score += 0.10
        sup.append("Error occurs at the very first step")

    if f.correct_count == 0 and f.error_count >= 2:
        score += 0.15
        sup.append("No correct answers at all")

    if f.correct_count > 0:
        con.append("Some correct answers — partial understanding exists")
        score -= 0.05

    if f.errors_structurally_similar and f.unique_error_signatures == 1:
        con.append("Single consistent error — looks more like a misconception than a broad gap")
        score -= 0.10

    return max(score, 0.0), sup, con


_SCORERS = {
    RootCauseCategory.MISCONCEPTION: _score_misconception,
    RootCauseCategory.CARELESS_ERROR: _score_careless,
    RootCauseCategory.COMPUTATIONAL_ERROR: _score_computational,
    RootCauseCategory.PROCEDURAL_GAP: _score_procedural_gap,
    RootCauseCategory.CONCEPTUAL_GAP: _score_conceptual_gap,
}


def generate_and_score_hypotheses(
    features: ErrorFeatures,
    case: EvaluationCaseInput,
) -> list[HypothesisDetail]:
    """
    Run every scorer, normalise scores into confidences, and return
    the hypotheses sorted by confidence descending.
    """
    raw: list[tuple[RootCauseCategory, float, list[str], list[str]]] = []
    for cat, scorer in _SCORERS.items():
        score, sup, con = scorer(features)
        raw.append((cat, score, sup, con))

    total = sum(s for _, s, _, _ in raw)
    hypotheses: list[HypothesisDetail] = []
    for cat, score, sup, con in raw:
        conf = score / total if total > 0 else 0.0
        # Attempt to find a specific label when the category is MISCONCEPTION
        specific: Optional[str] = None
        if cat == RootCauseCategory.MISCONCEPTION:
            specific = _identify_specific_misconception(features, case)
        hypotheses.append(
            HypothesisDetail(
                cause=cat,
                specific_label=specific,
                confidence=round(conf, 4),
                supporting_evidence=sup,
                contradicting_evidence=con,
                evidence_strength=round(score, 4),
            )
        )

    hypotheses.sort(key=lambda h: h.confidence, reverse=True)
    return hypotheses


def _identify_specific_misconception(
    features: ErrorFeatures,
    case: EvaluationCaseInput,
) -> Optional[str]:
    """
    If we believe the cause is a MISCONCEPTION, try to narrow it to a
    specific known misconception by checking which misconceptions are
    associated with the affected skills.

    This does NOT hard-code a mapping.  It queries the case's available
    misconceptions and returns the first one whose related skill appears
    in the set of skills that have errors.  This is a heuristic — the
    LLM evaluator can do much better.
    """
    if not case.available_misconceptions or not features.skills_with_errors:
        return None

    error_skill_names = set(s.lower() for s in features.skills_with_errors)
    for m in case.available_misconceptions:
        if m.related_skill_name.lower() in error_skill_names:
            return m.description
    return None


# ── 3.  Diagnosis Selection ───────────────────────────────────────────


def produce_independent_diagnosis(
    case: EvaluationCaseInput,
) -> IndependentDiagnosis:
    """
    End-to-end independent diagnosis: extract features → score
    hypotheses → select root cause → return structured result.
    """
    features = extract_error_features(case)
    hypotheses = generate_and_score_hypotheses(features, case)

    # ── Insufficient evidence gate ──
    if features.error_count < _MIN_EVIDENCE_FOR_DIAGNOSIS:
        return IndependentDiagnosis(
            observed_error=features.most_common_error or "unknown",
            skill_involved=", ".join(features.skills_with_errors) or "unknown",
            hypotheses=hypotheses,
            independent_root_cause=RootCauseCategory.INSUFFICIENT_EVIDENCE,
            confidence=0.0,
            evidence_summary=[
                f"Only {features.error_count} error(s) observed — "
                "insufficient to distinguish between competing explanations."
            ],
            most_informative_next_question=(
                "Repeat a similar question to determine whether the error is "
                "systematic or an isolated slip."
            ),
            error_features=features,
        )

    best = hypotheses[0]

    # Cap confidence when evidence is thin
    confidence = best.confidence
    if features.error_count <= 2:
        confidence = min(confidence, _CONFIDENCE_CAP_SINGLE_ERROR)

    # Compile a human-readable evidence summary
    evidence_summary = [f"Observed error: {features.most_common_error or 'unknown'}"]
    evidence_summary.extend(best.supporting_evidence)

    # Suggest the next most informative question
    next_q = _suggest_next_question(best, hypotheses, features, case)

    return IndependentDiagnosis(
        observed_error=features.most_common_error or "unknown",
        skill_involved=", ".join(features.skills_with_errors) or "unknown",
        hypotheses=hypotheses,
        independent_root_cause=best.cause,
        specific_label=best.specific_label,
        confidence=round(confidence, 4),
        evidence_summary=evidence_summary,
        most_informative_next_question=next_q,
        error_features=features,
    )


def _suggest_next_question(
    best: HypothesisDetail,
    all_hyps: list[HypothesisDetail],
    features: ErrorFeatures,
    case: EvaluationCaseInput,
) -> str:
    """
    Suggest a question that would best distinguish the top hypothesis
    from the runner-up.
    """
    if len(all_hyps) < 2:
        return "Ask another question on the same skill to gather more evidence."

    runner_up = all_hyps[1]

    # Generic suggestions based on category pairs
    pair = frozenset([best.cause, runner_up.cause])

    if pair == frozenset([RootCauseCategory.MISCONCEPTION, RootCauseCategory.CARELESS_ERROR]):
        return (
            "Re-test the same concept with a structurally similar problem. "
            "If the same error recurs, it is unlikely to be careless."
        )
    if pair == frozenset(
        [RootCauseCategory.MISCONCEPTION, RootCauseCategory.COMPUTATIONAL_ERROR]
    ):
        return (
            "Present the same algebraic structure with simpler numbers. "
            "If the error persists, it is conceptual rather than arithmetic."
        )
    if pair == frozenset(
        [RootCauseCategory.CONCEPTUAL_GAP, RootCauseCategory.PROCEDURAL_GAP]
    ):
        return (
            "Ask the student to explain the rule or concept verbally, "
            "or present a recognition task rather than a production task."
        )

    return (
        f"Ask a question designed to distinguish "
        f"{best.cause.value} from {runner_up.cause.value}."
    )
