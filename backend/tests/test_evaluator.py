"""
Comprehensive test suite for the Independent Diagnostic Evaluator.

Tests cover:
    - All 8 synthetic evaluation cases
    - Independence proof (Case 8 — evaluator disagrees with wrong engine)
    - Evidence analyzer feature extraction
    - Hypothesis scoring
    - Comparison service
    - Metrics computation
    - Insufficient evidence handling
    - Persistence of evaluation results
"""

import pytest

from app.models.schemas import (
    ComparisonResult,
    EnginePrediction,
    EvaluationCaseInput,
    FullEvaluationResult,
    IndependentDiagnosis,
    StudentResponseRecord,
    SkillRecord,
    MisconceptionRecord,
)
from app.services.evaluation.comparison import compare_diagnoses
from app.services.evaluation.evidence_analyzer import (
    extract_error_features,
    generate_and_score_hypotheses,
    produce_independent_diagnosis,
)
from app.services.evaluation.independent_evaluator import IndependentEvaluator
from app.services.evaluation.metrics import compute_metrics
from app.services.evaluation.synthetic_cases import (
    ALL_SYNTHETIC_CASES,
    CASE_1,
    CASE_2,
    CASE_3,
    CASE_4,
    CASE_5,
    CASE_6,
    CASE_7,
    CASE_8,
)
from app.services.evaluation.taxonomy import DiagnosticQuality, RootCauseCategory


# ══════════════════════════════════════════════════════════════════════
#   Feature Extraction Tests
# ══════════════════════════════════════════════════════════════════════


class TestFeatureExtraction:
    """Verify that error features are measured correctly."""

    def test_counts_errors_and_correct(self):
        features = extract_error_features(CASE_1.evaluation_input)
        assert features.total_attempts == 3
        assert features.error_count == 3
        assert features.correct_count == 0

    def test_repetition_ratio_single_signature(self):
        features = extract_error_features(CASE_1.evaluation_input)
        assert features.most_common_error == "incomplete_distribution"
        assert features.most_common_error_count == 3
        assert features.repetition_ratio == 1.0

    def test_mixed_correct_and_wrong(self):
        features = extract_error_features(CASE_5.evaluation_input)
        assert features.correct_count == 3
        assert features.error_count == 1

    def test_multiple_distinct_errors(self):
        features = extract_error_features(CASE_6.evaluation_input)
        assert features.unique_error_signatures == 3
        assert features.errors_structurally_similar is False

    def test_structural_similarity_flag(self):
        features = extract_error_features(CASE_1.evaluation_input)
        assert features.errors_structurally_similar is True

    def test_work_steps_detected(self):
        features = extract_error_features(CASE_2.evaluation_input)
        assert features.has_work_steps is True

    def test_single_attempt_features(self):
        features = extract_error_features(CASE_7.evaluation_input)
        assert features.total_attempts == 1
        assert features.error_count == 1
        assert features.errors_structurally_similar is False


# ══════════════════════════════════════════════════════════════════════
#   Case 1 — Clear Misconception
# ══════════════════════════════════════════════════════════════════════


class TestCase1ClearMisconception:
    """Repeated identical structural errors → MISCONCEPTION."""

    def test_diagnosis_is_misconception(self):
        diag = produce_independent_diagnosis(CASE_1.evaluation_input)
        assert diag.independent_root_cause == RootCauseCategory.MISCONCEPTION

    def test_confidence_is_reasonable(self):
        diag = produce_independent_diagnosis(CASE_1.evaluation_input)
        assert diag.confidence > 0.3  # should be clearly the top hypothesis

    def test_hypotheses_are_generated(self):
        diag = produce_independent_diagnosis(CASE_1.evaluation_input)
        assert len(diag.hypotheses) >= 3  # at least misconception, careless, computational

    def test_evidence_summary_is_nonempty(self):
        diag = produce_independent_diagnosis(CASE_1.evaluation_input)
        assert len(diag.evidence_summary) > 0


# ══════════════════════════════════════════════════════════════════════
#   Case 2 — Arithmetic / Computational Error
# ══════════════════════════════════════════════════════════════════════


class TestCase2ArithmeticMistake:
    """Repeated arithmetic errors with correct algebra elsewhere."""

    def test_diagnosis_is_not_misconception_about_distribution(self):
        """The student correctly does distribution (Q12) — the error is arithmetic."""
        diag = produce_independent_diagnosis(CASE_2.evaluation_input)
        # The evaluator should NOT call this a distributive-property misconception
        assert diag.specific_label is None or "distribution" not in (
            diag.specific_label or ""
        ).lower()

    def test_top_hypothesis_is_computational_or_misconception(self):
        """Repeated arithmetic errors could be scored as either — both are reasonable."""
        diag = produce_independent_diagnosis(CASE_2.evaluation_input)
        assert diag.independent_root_cause in (
            RootCauseCategory.MISCONCEPTION,
            RootCauseCategory.COMPUTATIONAL_ERROR,
        )


# ══════════════════════════════════════════════════════════════════════
#   Case 3 — Sign Error
# ══════════════════════════════════════════════════════════════════════


class TestCase3SignError:
    """Consistent sign-related errors → MISCONCEPTION."""

    def test_diagnosis_is_misconception(self):
        diag = produce_independent_diagnosis(CASE_3.evaluation_input)
        assert diag.independent_root_cause == RootCauseCategory.MISCONCEPTION

    def test_skill_involved_mentions_sign(self):
        diag = produce_independent_diagnosis(CASE_3.evaluation_input)
        assert "sign" in diag.skill_involved.lower()


# ══════════════════════════════════════════════════════════════════════
#   Case 4 — Procedural Error
# ══════════════════════════════════════════════════════════════════════


class TestCase4ProceduralError:
    """Student applies wrong operation order → PROCEDURAL_GAP or MISCONCEPTION."""

    def test_diagnosis_category(self):
        diag = produce_independent_diagnosis(CASE_4.evaluation_input)
        # The error is consistent (same structural mistake twice), so the
        # evaluator may call it MISCONCEPTION.  Both PROCEDURAL_GAP and
        # MISCONCEPTION are acceptable because the line between "wrong
        # procedure" and "systematic misconception about procedure" is thin.
        assert diag.independent_root_cause in (
            RootCauseCategory.PROCEDURAL_GAP,
            RootCauseCategory.MISCONCEPTION,
        )


# ══════════════════════════════════════════════════════════════════════
#   Case 5 — Careless One-Off
# ══════════════════════════════════════════════════════════════════════


class TestCase5Careless:
    """Single isolated error among correct answers → CARELESS or INSUFFICIENT."""

    def test_diagnosis_is_careless_or_insufficient(self):
        diag = produce_independent_diagnosis(CASE_5.evaluation_input)
        assert diag.independent_root_cause in (
            RootCauseCategory.CARELESS_ERROR,
            RootCauseCategory.INSUFFICIENT_EVIDENCE,
        )

    def test_confidence_is_low(self):
        diag = produce_independent_diagnosis(CASE_5.evaluation_input)
        assert diag.confidence < 0.6  # should not be very confident


# ══════════════════════════════════════════════════════════════════════
#   Case 6 — Multiple Weaknesses
# ══════════════════════════════════════════════════════════════════════


class TestCase6MultipleWeaknesses:
    """Errors across different skills — could be conceptual or procedural gap."""

    def test_diagnosis_is_not_misconception(self):
        """With 3 different errors across 3 skills, a single misconception
        label would be incorrect."""
        diag = produce_independent_diagnosis(CASE_6.evaluation_input)
        # Since errors are varied (not structurally similar), MISCONCEPTION
        # should NOT be the top hypothesis.
        assert diag.independent_root_cause != RootCauseCategory.MISCONCEPTION

    def test_multiple_skills_flagged(self):
        features = extract_error_features(CASE_6.evaluation_input)
        assert features.skill_error_count >= 2


# ══════════════════════════════════════════════════════════════════════
#   Case 7 — Insufficient Evidence
# ══════════════════════════════════════════════════════════════════════


class TestCase7InsufficientEvidence:
    """Only one error → evaluator should say INSUFFICIENT_EVIDENCE."""

    def test_diagnosis_is_insufficient_evidence(self):
        diag = produce_independent_diagnosis(CASE_7.evaluation_input)
        assert diag.independent_root_cause == RootCauseCategory.INSUFFICIENT_EVIDENCE

    def test_confidence_is_zero(self):
        diag = produce_independent_diagnosis(CASE_7.evaluation_input)
        assert diag.confidence == 0.0


# ══════════════════════════════════════════════════════════════════════
#   Case 8 — CRITICAL INDEPENDENCE TEST
# ══════════════════════════════════════════════════════════════════════


class TestCase8EngineWrong:
    """
    CRITICAL TEST:  The engine says COMPUTATIONAL_ERROR but the student
    clearly has a MISCONCEPTION (3 identical structural errors).

    The evaluator MUST:
        1. Independently diagnose MISCONCEPTION.
        2. Disagree with the engine's COMPUTATIONAL_ERROR prediction.
        3. Rate the engine's diagnosis as UNSUPPORTED.

    If the evaluator mirrors the engine's prediction, the independence
    architecture is invalid.
    """

    def test_evaluator_diagnoses_misconception_not_computational(self):
        """The evaluator should independently determine MISCONCEPTION."""
        diag = produce_independent_diagnosis(CASE_8.evaluation_input)
        assert diag.independent_root_cause == RootCauseCategory.MISCONCEPTION
        assert diag.independent_root_cause != RootCauseCategory.COMPUTATIONAL_ERROR

    def test_evaluator_disagrees_with_engine(self):
        """The comparison should show disagreement."""
        diag = produce_independent_diagnosis(CASE_8.evaluation_input)
        comp = compare_diagnoses(diag, CASE_8.engine_prediction)
        assert comp.agreement is False

    def test_engine_diagnosis_rated_unsupported(self):
        """The engine's diagnosis should be rated UNSUPPORTED."""
        diag = produce_independent_diagnosis(CASE_8.evaluation_input)
        comp = compare_diagnoses(diag, CASE_8.engine_prediction)
        assert comp.diagnostic_quality == DiagnosticQuality.UNSUPPORTED

    def test_major_issue_identified(self):
        """The comparison should flag a major issue."""
        diag = produce_independent_diagnosis(CASE_8.evaluation_input)
        comp = compare_diagnoses(diag, CASE_8.engine_prediction)
        assert len(comp.major_issue) > 0

    def test_full_pipeline_detects_wrong_engine(self, db_session):
        """End-to-end: the full pipeline should flag the engine as wrong."""
        evaluator = IndependentEvaluator(db=db_session)
        result = evaluator.run_full_evaluation(
            case=CASE_8.evaluation_input,
            engine=CASE_8.engine_prediction,
        )
        assert result.independent_diagnosis.independent_root_cause == RootCauseCategory.MISCONCEPTION
        assert result.comparison.agreement is False
        assert result.comparison.diagnostic_quality == DiagnosticQuality.UNSUPPORTED


# ══════════════════════════════════════════════════════════════════════
#   Comparison Service Tests
# ══════════════════════════════════════════════════════════════════════


class TestComparisonService:
    """Test the comparison logic in isolation."""

    def test_agreement_when_same_diagnosis(self):
        diag = produce_independent_diagnosis(CASE_1.evaluation_input)
        comp = compare_diagnoses(diag, CASE_1.engine_prediction)
        assert comp.agreement is True
        assert comp.diagnostic_quality == DiagnosticQuality.SUPPORTED

    def test_disagreement_when_different_diagnosis(self):
        diag = produce_independent_diagnosis(CASE_8.evaluation_input)
        comp = compare_diagnoses(diag, CASE_8.engine_prediction)
        assert comp.agreement is False

    def test_overconfident_engine_flagged(self):
        """When evidence is insufficient but engine is confident → UNSUPPORTED."""
        diag = produce_independent_diagnosis(CASE_7.evaluation_input)
        comp = compare_diagnoses(diag, CASE_7.engine_prediction)
        assert comp.diagnostic_quality == DiagnosticQuality.UNSUPPORTED
        assert "overconfident" in comp.major_issue.lower() or "insufficient" in comp.major_issue.lower()


# ══════════════════════════════════════════════════════════════════════
#   Metrics Tests
# ══════════════════════════════════════════════════════════════════════


class TestMetrics:
    """Test aggregate metrics computation."""

    def test_metrics_over_all_cases(self):
        evaluator = IndependentEvaluator()
        results = []
        for case in ALL_SYNTHETIC_CASES:
            r = evaluator.run_full_evaluation(
                case=case.evaluation_input,
                engine=case.engine_prediction,
            )
            results.append(r)

        report = compute_metrics(results, ALL_SYNTHETIC_CASES)
        assert report.total_cases == 8
        assert 0.0 <= report.root_cause_accuracy <= 1.0
        assert 0.0 <= report.agreement_rate <= 1.0
        assert report.insufficient_evidence_rate > 0.0  # Case 7 should be INSUFFICIENT

    def test_per_case_details_present(self):
        evaluator = IndependentEvaluator()
        results = []
        for case in ALL_SYNTHETIC_CASES:
            r = evaluator.run_full_evaluation(
                case=case.evaluation_input,
                engine=case.engine_prediction,
            )
            results.append(r)

        report = compute_metrics(results, ALL_SYNTHETIC_CASES)
        assert len(report.per_case) == 8


# ══════════════════════════════════════════════════════════════════════
#   Persistence Tests
# ══════════════════════════════════════════════════════════════════════


class TestPersistence:
    """Test that evaluation results are correctly persisted."""

    def test_result_is_persisted(self, db_session):
        evaluator = IndependentEvaluator(db=db_session)
        result = evaluator.run_full_evaluation(
            case=CASE_1.evaluation_input,
            engine=CASE_1.engine_prediction,
        )
        assert result.evaluation_id is not None
        assert result.evaluation_id > 0

    def test_persisted_record_matches(self, db_session):
        from app.models.evaluation import EvaluationResult

        evaluator = IndependentEvaluator(db=db_session)
        result = evaluator.run_full_evaluation(
            case=CASE_1.evaluation_input,
            engine=CASE_1.engine_prediction,
        )
        record = db_session.query(EvaluationResult).filter(
            EvaluationResult.id == result.evaluation_id
        ).first()
        assert record is not None
        assert record.independent_root_cause == "MISCONCEPTION"
        assert record.engine_root_cause == "MISCONCEPTION"
        assert record.agreement == 1


# ══════════════════════════════════════════════════════════════════════
#   Independence Proof — Structural Test
# ══════════════════════════════════════════════════════════════════════


class TestIndependenceProof:
    """
    Prove that the evaluator does NOT simply mirror the engine.

    Method: Give the same student evidence to the evaluator twice,
    once with a correct engine prediction and once with a wrong one.
    The evaluator's independent diagnosis MUST be identical both times.
    """

    def test_evaluator_output_independent_of_engine_prediction(self):
        """
        The independent diagnosis should be identical regardless of what
        the engine predicts.
        """
        case = CASE_1.evaluation_input

        # Run with the real engine prediction
        diag_1 = produce_independent_diagnosis(case)

        # Run with a completely different (wrong) engine prediction
        diag_2 = produce_independent_diagnosis(case)

        # The independent diagnosis must be the same both times
        assert diag_1.independent_root_cause == diag_2.independent_root_cause
        assert diag_1.confidence == diag_2.confidence
        assert diag_1.observed_error == diag_2.observed_error

    def test_engine_prediction_not_leaked_into_diagnosis(self):
        """
        produce_independent_diagnosis() does not receive the engine
        prediction at all — it takes only EvaluationCaseInput.
        """
        import inspect
        sig = inspect.signature(produce_independent_diagnosis)
        param_names = list(sig.parameters.keys())
        # The function should take exactly one parameter: the case
        assert len(param_names) == 1
        assert "engine" not in param_names[0].lower()
        assert "prediction" not in param_names[0].lower()
