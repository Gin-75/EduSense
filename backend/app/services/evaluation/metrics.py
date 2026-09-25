"""
Evaluation Metrics — aggregate quality metrics over a set of evaluations.

Ground-truth labels come from manually defined synthetic cases.
"""

from __future__ import annotations

from app.models.schemas import (
    EvaluationMetricsReport,
    FullEvaluationResult,
    SyntheticCaseDefinition,
)
from app.services.evaluation.taxonomy import RootCauseCategory


def compute_metrics(
    results: list[FullEvaluationResult],
    ground_truths: list[SyntheticCaseDefinition],
) -> EvaluationMetricsReport:
    """
    Compute aggregate metrics by comparing evaluation results to
    synthetic ground-truth labels.

    ``results`` and ``ground_truths`` must be aligned by index or by
    ``case_id``.  We align by ``case_id`` for safety.
    """
    gt_map: dict[str, SyntheticCaseDefinition] = {g.case_id: g for g in ground_truths}

    total = len(results)
    if total == 0:
        return EvaluationMetricsReport()

    correct_top1 = 0
    correct_top2 = 0
    agreements = 0
    false_diag = 0
    insufficient = 0
    confidences: list[float] = []
    conf_correct: list[float] = []
    conf_wrong: list[float] = []
    q_counts: list[int] = []
    per_case: list[dict] = []

    for r in results:
        diag = r.independent_diagnosis
        comp = r.comparison
        cid = r.case_id or ""
        gt = gt_map.get(cid)

        is_correct = False
        if gt:
            is_correct = diag.independent_root_cause == gt.ground_truth_root_cause

        # Top-1 accuracy
        if is_correct:
            correct_top1 += 1

        # Top-2 accuracy: is the ground truth in the top 2 hypotheses?
        top_2_cats = [h.cause for h in diag.hypotheses[:2]]
        if gt and gt.ground_truth_root_cause in top_2_cats:
            correct_top2 += 1

        # Agreement with engine
        if comp and comp.agreement:
            agreements += 1

        # False diagnosis: confident but wrong
        if (
            not is_correct
            and diag.independent_root_cause != RootCauseCategory.INSUFFICIENT_EVIDENCE
            and diag.confidence >= 0.4
        ):
            false_diag += 1

        # Insufficient evidence rate
        if diag.independent_root_cause == RootCauseCategory.INSUFFICIENT_EVIDENCE:
            insufficient += 1

        confidences.append(diag.confidence)
        if is_correct:
            conf_correct.append(diag.confidence)
        else:
            conf_wrong.append(diag.confidence)

        # Questions to diagnosis (count of diagnostic history entries in the case input)
        # We don't have direct access to the case input here, so count attempts
        q_counts.append(len(diag.hypotheses))  # proxy: number of hypotheses evaluated

        per_case.append(
            {
                "case_id": cid,
                "independent": diag.independent_root_cause.value,
                "ground_truth": gt.ground_truth_root_cause.value if gt else "N/A",
                "correct": is_correct,
                "confidence": diag.confidence,
                "agreement_with_engine": comp.agreement if comp else None,
            }
        )

    return EvaluationMetricsReport(
        total_cases=total,
        root_cause_accuracy=correct_top1 / total,
        top_2_accuracy=correct_top2 / total,
        agreement_rate=agreements / total,
        false_diagnosis_rate=false_diag / total,
        insufficient_evidence_rate=insufficient / total,
        average_confidence=sum(confidences) / len(confidences) if confidences else 0.0,
        confidence_when_correct=(
            sum(conf_correct) / len(conf_correct) if conf_correct else 0.0
        ),
        confidence_when_wrong=(
            sum(conf_wrong) / len(conf_wrong) if conf_wrong else 0.0
        ),
        average_questions_to_diagnosis=(
            sum(q_counts) / len(q_counts) if q_counts else 0.0
        ),
        per_case=per_case,
    )
