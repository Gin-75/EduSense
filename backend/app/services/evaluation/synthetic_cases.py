"""
Synthetic Evaluation Cases — 8 controlled scenarios with known ground truths.

These cases exercise the evaluator's ability to independently diagnose
root causes and, critically, to disagree with the engine when the engine
is wrong (Case 8).
"""

from app.models.schemas import (
    DiagnosticQuestionRecord,
    EnginePrediction,
    EvaluationCaseInput,
    MisconceptionRecord,
    SkillRecord,
    StudentResponseRecord,
    SyntheticCaseDefinition,
)
from app.services.evaluation.taxonomy import RootCauseCategory

# ── Shared skills & misconceptions ────────────────────────────────────

_SKILLS = [
    SkillRecord(id=1, name="Distributive Property", subject="Algebra", difficulty=0.4),
    SkillRecord(id=2, name="Integer Arithmetic", subject="Arithmetic", difficulty=0.2),
    SkillRecord(id=3, name="Sign Manipulation", subject="Algebra", difficulty=0.3),
    SkillRecord(id=4, name="Inverse Operations", subject="Algebra", difficulty=0.4),
    SkillRecord(id=5, name="Combining Like Terms", subject="Algebra", difficulty=0.35),
    SkillRecord(id=6, name="Linear Equations", subject="Algebra", difficulty=0.5),
    SkillRecord(id=7, name="Fractions", subject="Arithmetic", difficulty=0.3),
]

_MISCONCEPTIONS = [
    MisconceptionRecord(
        id=1,
        description="Coefficient applied to first term only (incomplete distribution)",
        related_skill_id=1,
        related_skill_name="Distributive Property",
    ),
    MisconceptionRecord(
        id=2,
        description="Subtracting a negative treated as subtracting a positive",
        related_skill_id=3,
        related_skill_name="Sign Manipulation",
    ),
    MisconceptionRecord(
        id=3,
        description="Adding instead of multiplying for repeated addition",
        related_skill_id=2,
        related_skill_name="Integer Arithmetic",
    ),
]


# ── Case 1: Clear distributive-property misconception ─────────────────

CASE_1 = SyntheticCaseDefinition(
    case_id="case_1_clear_misconception",
    description="Student repeatedly applies coefficient to only the first term inside parentheses.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_1_clear_misconception",
        student_responses=[
            StudentResponseRecord(
                question_id=1,
                question_content="Expand: 2(x + 3)",
                expected_answer="2x + 6",
                student_answer="2x + 3",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=2,
                question_content="Expand: 3(x + 4)",
                expected_answer="3x + 12",
                student_answer="3x + 4",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=3,
                question_content="Expand: 4(x + 2)",
                expected_answer="4x + 8",
                student_answer="4x + 2",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
        diagnostic_history=[
            DiagnosticQuestionRecord(
                question_id=2,
                question_content="Expand: 3(x + 4)",
                purpose="Test distributive property with different numbers",
                student_answer="3x + 4",
                is_correct=False,
                error_signature="incomplete_distribution",
            ),
            DiagnosticQuestionRecord(
                question_id=3,
                question_content="Expand: 4(x + 2)",
                purpose="Confirm distributive property misconception",
                student_answer="4x + 2",
                is_correct=False,
                error_signature="incomplete_distribution",
            ),
        ],
    ),
    engine_prediction=EnginePrediction(
        root_cause="MISCONCEPTION",
        confidence=0.88,
        diagnosis_detail="Incomplete distribution — coefficient applied to first term only",
    ),
    ground_truth_root_cause=RootCauseCategory.MISCONCEPTION,
    ground_truth_specific_label="incomplete_distribution",
)


# ── Case 2: Simple arithmetic mistake ────────────────────────────────

CASE_2 = SyntheticCaseDefinition(
    case_id="case_2_arithmetic_mistake",
    description="Student correctly applies algebra but makes arithmetic errors in computation.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_2_arithmetic_mistake",
        student_responses=[
            StudentResponseRecord(
                question_id=10,
                question_content="Solve: x + 7 = 15",
                expected_answer="8",
                student_answer="9",
                is_correct=False,
                error_signature="arithmetic_subtraction_error",
                skill_ids=[2, 6],
                skill_names=["Integer Arithmetic", "Linear Equations"],
                student_work_steps=["x = 15 - 7", "x = 9"],
            ),
            StudentResponseRecord(
                question_id=11,
                question_content="Solve: x + 5 = 12",
                expected_answer="7",
                student_answer="8",
                is_correct=False,
                error_signature="arithmetic_subtraction_error",
                skill_ids=[2, 6],
                skill_names=["Integer Arithmetic", "Linear Equations"],
                student_work_steps=["x = 12 - 5", "x = 8"],
            ),
            StudentResponseRecord(
                question_id=12,
                question_content="Expand: 2(x + 3)",
                expected_answer="2x + 6",
                student_answer="2x + 6",
                is_correct=True,
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="COMPUTATIONAL_ERROR",
        confidence=0.72,
        diagnosis_detail="Repeated arithmetic subtraction errors",
    ),
    ground_truth_root_cause=RootCauseCategory.COMPUTATIONAL_ERROR,
)


# ── Case 3: Sign error ───────────────────────────────────────────────

CASE_3 = SyntheticCaseDefinition(
    case_id="case_3_sign_error",
    description="Student consistently treats subtraction of negatives as subtraction of positives.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_3_sign_error",
        student_responses=[
            StudentResponseRecord(
                question_id=20,
                question_content="Simplify: 5 - (-3)",
                expected_answer="8",
                student_answer="2",
                is_correct=False,
                error_signature="sign_negation_error",
                skill_ids=[3],
                skill_names=["Sign Manipulation"],
            ),
            StudentResponseRecord(
                question_id=21,
                question_content="Simplify: 10 - (-2)",
                expected_answer="12",
                student_answer="8",
                is_correct=False,
                error_signature="sign_negation_error",
                skill_ids=[3],
                skill_names=["Sign Manipulation"],
            ),
            StudentResponseRecord(
                question_id=22,
                question_content="Simplify: 3 + 4",
                expected_answer="7",
                student_answer="7",
                is_correct=True,
                skill_ids=[2],
                skill_names=["Integer Arithmetic"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="MISCONCEPTION",
        confidence=0.80,
        diagnosis_detail="Subtracting a negative treated as subtracting a positive",
    ),
    ground_truth_root_cause=RootCauseCategory.MISCONCEPTION,
    ground_truth_specific_label="sign_negation_error",
)


# ── Case 4: Procedural equation-solving error ────────────────────────

CASE_4 = SyntheticCaseDefinition(
    case_id="case_4_procedural_error",
    description="Student performs operations in wrong order when solving multi-step equations.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_4_procedural_error",
        student_responses=[
            StudentResponseRecord(
                question_id=30,
                question_content="Solve: 2x + 3 = 11",
                expected_answer="4",
                student_answer="7",
                is_correct=False,
                error_signature="wrong_operation_order",
                skill_ids=[4, 6],
                skill_names=["Inverse Operations", "Linear Equations"],
                student_work_steps=["2x = 11 + 3", "2x = 14", "x = 7"],
            ),
            StudentResponseRecord(
                question_id=31,
                question_content="Solve: 3x + 5 = 20",
                expected_answer="5",
                student_answer="25/3",
                is_correct=False,
                error_signature="wrong_operation_order",
                skill_ids=[4, 6],
                skill_names=["Inverse Operations", "Linear Equations"],
                student_work_steps=["3x = 20 + 5", "3x = 25", "x = 25/3"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="PROCEDURAL_GAP",
        confidence=0.75,
        diagnosis_detail="Student adds instead of subtracting when isolating x",
    ),
    ground_truth_root_cause=RootCauseCategory.PROCEDURAL_GAP,
)


# ── Case 5: Careless one-off mistake ─────────────────────────────────

CASE_5 = SyntheticCaseDefinition(
    case_id="case_5_careless",
    description="Student answers many questions correctly but makes one isolated error.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_5_careless",
        student_responses=[
            StudentResponseRecord(
                question_id=40,
                question_content="Expand: 2(x + 5)",
                expected_answer="2x + 10",
                student_answer="2x + 10",
                is_correct=True,
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=41,
                question_content="Solve: x + 3 = 10",
                expected_answer="7",
                student_answer="7",
                is_correct=True,
                skill_ids=[6],
                skill_names=["Linear Equations"],
            ),
            StudentResponseRecord(
                question_id=42,
                question_content="Expand: 3(x + 2)",
                expected_answer="3x + 6",
                student_answer="3x + 5",
                is_correct=False,
                error_signature="arithmetic_multiplication_error",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=43,
                question_content="Simplify: 5 - (-2)",
                expected_answer="7",
                student_answer="7",
                is_correct=True,
                skill_ids=[3],
                skill_names=["Sign Manipulation"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="CARELESS_ERROR",
        confidence=0.60,
        diagnosis_detail="Isolated arithmetic error in otherwise strong performance",
    ),
    ground_truth_root_cause=RootCauseCategory.CARELESS_ERROR,
)


# ── Case 6: Multiple simultaneous weaknesses ─────────────────────────

CASE_6 = SyntheticCaseDefinition(
    case_id="case_6_multiple_weaknesses",
    description="Student shows errors across multiple different skills — no single clear root cause.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_6_multiple_weaknesses",
        student_responses=[
            StudentResponseRecord(
                question_id=50,
                question_content="Expand: 2(x + 3)",
                expected_answer="2x + 6",
                student_answer="2x + 3",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=51,
                question_content="Simplify: 5 - (-3)",
                expected_answer="8",
                student_answer="2",
                is_correct=False,
                error_signature="sign_negation_error",
                skill_ids=[3],
                skill_names=["Sign Manipulation"],
            ),
            StudentResponseRecord(
                question_id=52,
                question_content="Solve: x + 7 = 15",
                expected_answer="8",
                student_answer="9",
                is_correct=False,
                error_signature="arithmetic_subtraction_error",
                skill_ids=[2, 6],
                skill_names=["Integer Arithmetic", "Linear Equations"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="CONCEPTUAL_GAP",
        confidence=0.65,
        diagnosis_detail="Broad algebra weakness",
    ),
    ground_truth_root_cause=RootCauseCategory.CONCEPTUAL_GAP,
)


# ── Case 7: Insufficient evidence ────────────────────────────────────

CASE_7 = SyntheticCaseDefinition(
    case_id="case_7_insufficient_evidence",
    description="Only one ambiguous error — not enough data to diagnose.",
    evaluation_input=EvaluationCaseInput(
        case_id="case_7_insufficient_evidence",
        student_responses=[
            StudentResponseRecord(
                question_id=60,
                question_content="Expand: 2(x + 3)",
                expected_answer="2x + 6",
                student_answer="2x + 3",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="MISCONCEPTION",
        confidence=0.70,
        diagnosis_detail="Incomplete distribution",
    ),
    ground_truth_root_cause=RootCauseCategory.INSUFFICIENT_EVIDENCE,
)


# ── Case 8: Engine intentionally WRONG ────────────────────────────────
# The student clearly has a distributive-property misconception, but
# the engine incorrectly diagnoses it as COMPUTATIONAL_ERROR.  The
# evaluator MUST detect this disagreement.

CASE_8 = SyntheticCaseDefinition(
    case_id="case_8_engine_wrong",
    description=(
        "Student clearly has a distributive-property misconception "
        "(3 identical structural errors) but the engine incorrectly "
        "predicts COMPUTATIONAL_ERROR."
    ),
    evaluation_input=EvaluationCaseInput(
        case_id="case_8_engine_wrong",
        student_responses=[
            StudentResponseRecord(
                question_id=70,
                question_content="Expand: 2(x + 3)",
                expected_answer="2x + 6",
                student_answer="2x + 3",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=71,
                question_content="Expand: 5(x + 1)",
                expected_answer="5x + 5",
                student_answer="5x + 1",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
            StudentResponseRecord(
                question_id=72,
                question_content="Expand: 4(x + 7)",
                expected_answer="4x + 28",
                student_answer="4x + 7",
                is_correct=False,
                error_signature="incomplete_distribution",
                skill_ids=[1],
                skill_names=["Distributive Property"],
            ),
        ],
        available_skills=_SKILLS,
        available_misconceptions=_MISCONCEPTIONS,
    ),
    engine_prediction=EnginePrediction(
        root_cause="COMPUTATIONAL_ERROR",  # ← intentionally WRONG
        confidence=0.75,
        diagnosis_detail="Arithmetic multiplication error",
    ),
    ground_truth_root_cause=RootCauseCategory.MISCONCEPTION,
    ground_truth_specific_label="incomplete_distribution",
)


# ── Registry ──────────────────────────────────────────────────────────

ALL_SYNTHETIC_CASES: list[SyntheticCaseDefinition] = [
    CASE_1,
    CASE_2,
    CASE_3,
    CASE_4,
    CASE_5,
    CASE_6,
    CASE_7,
    CASE_8,
]


def get_case_by_id(case_id: str) -> SyntheticCaseDefinition | None:
    """Look up a synthetic case by its ID."""
    for case in ALL_SYNTHETIC_CASES:
        if case.case_id == case_id:
            return case
    return None
