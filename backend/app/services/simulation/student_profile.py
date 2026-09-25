"""
Synthetic Student Profiles and Archetypes.

Defines the latent knowledge state and behavioral parameters of simulated students.
The Diagnostic Engine MUST NEVER receive these directly.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.simulation.ground_truth import GroundTruth

class StudentBehavior(BaseModel):
    careless_error_rate: float = 0.05
    guessing_rate: float = 0.02
    persistence: float = 1.0  # Used by LLM mode to determine if they give up
    response_style: str = "direct"  # e.g., "shows_work", "direct"

class SyntheticStudentProfile(BaseModel):
    student_id: str
    archetype: str
    skill_mastery: Dict[str, float]  # Skill name to mastery probability [0, 1]
    misconceptions: List[str] = Field(default_factory=list)
    confidence_by_skill: Dict[str, float] = Field(default_factory=dict)
    behavior: StudentBehavior = Field(default_factory=StudentBehavior)
    ground_truth: GroundTruth


# --- Archetype Definitions ---

def create_strong_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Strong Student",
        skill_mastery={"distributive_property": 0.95, "integer_arithmetic": 0.98, "linear_equations": 0.95, "sign_manipulation": 0.95, "inverse_operations": 0.95},
        behavior=StudentBehavior(careless_error_rate=0.01, guessing_rate=0.01),
        ground_truth=GroundTruth(category="CARELESS_ERROR", specific_cause=None, affected_skills=[])
    )

def create_distributive_misconception_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Distributive Misconception",
        skill_mastery={"distributive_property": 0.1, "integer_arithmetic": 0.9, "linear_equations": 0.8, "sign_manipulation": 0.9, "inverse_operations": 0.9},
        misconceptions=["incomplete_distribution"],
        behavior=StudentBehavior(careless_error_rate=0.05),
        ground_truth=GroundTruth(category="MISCONCEPTION", specific_cause="incomplete_distribution", affected_skills=["distributive_property"])
    )

def create_arithmetic_weakness_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Arithmetic Weakness",
        skill_mastery={"distributive_property": 0.9, "integer_arithmetic": 0.3, "linear_equations": 0.8, "sign_manipulation": 0.9, "inverse_operations": 0.8},
        behavior=StudentBehavior(careless_error_rate=0.1),
        ground_truth=GroundTruth(category="COMPUTATIONAL_ERROR", affected_skills=["integer_arithmetic"])
    )

def create_sign_misconception_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Sign Misconception",
        skill_mastery={"distributive_property": 0.8, "integer_arithmetic": 0.8, "linear_equations": 0.8, "sign_manipulation": 0.1, "inverse_operations": 0.8},
        misconceptions=["sign_negation_error"],
        behavior=StudentBehavior(careless_error_rate=0.05),
        ground_truth=GroundTruth(category="MISCONCEPTION", specific_cause="sign_negation_error", affected_skills=["sign_manipulation"])
    )

def create_procedural_gap_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Equation Solving Procedural Gap",
        skill_mastery={"distributive_property": 0.9, "integer_arithmetic": 0.9, "linear_equations": 0.2, "sign_manipulation": 0.9, "inverse_operations": 0.2},
        misconceptions=["wrong_operation_order"],
        behavior=StudentBehavior(careless_error_rate=0.05),
        ground_truth=GroundTruth(category="PROCEDURAL_GAP", specific_cause="wrong_operation_order", affected_skills=["linear_equations", "inverse_operations"])
    )

def create_careless_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Careless Error Student",
        skill_mastery={"distributive_property": 0.85, "integer_arithmetic": 0.85, "linear_equations": 0.85, "sign_manipulation": 0.85, "inverse_operations": 0.85},
        behavior=StudentBehavior(careless_error_rate=0.25, guessing_rate=0.05), # High careless rate
        ground_truth=GroundTruth(category="CARELESS_ERROR", affected_skills=[])
    )

def create_multiple_weaknesses_student(student_id: str) -> SyntheticStudentProfile:
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Multiple Weaknesses",
        skill_mastery={"distributive_property": 0.4, "integer_arithmetic": 0.4, "linear_equations": 0.4, "sign_manipulation": 0.4, "inverse_operations": 0.4},
        behavior=StudentBehavior(careless_error_rate=0.1),
        ground_truth=GroundTruth(category="CONCEPTUAL_GAP", affected_skills=["distributive_property", "integer_arithmetic", "sign_manipulation", "linear_equations", "inverse_operations"])
    )

def create_insufficient_evidence_student(student_id: str) -> SyntheticStudentProfile:
    # A student who answers correctly a lot but we cap max_questions low, 
    # or they have weird latent state that can't be pinned down quickly.
    # We will simulate this by forcing the engine budget low or them being perfectly median.
    return SyntheticStudentProfile(
        student_id=student_id,
        archetype="Insufficient Evidence",
        skill_mastery={"distributive_property": 0.5, "integer_arithmetic": 0.5, "linear_equations": 0.5, "sign_manipulation": 0.5, "inverse_operations": 0.5},
        behavior=StudentBehavior(careless_error_rate=0.1),
        ground_truth=GroundTruth(category="INSUFFICIENT_EVIDENCE", affected_skills=[])
    )

def get_all_archetype_factories():
    return [
        create_strong_student,
        create_distributive_misconception_student,
        create_arithmetic_weakness_student,
        create_sign_misconception_student,
        create_procedural_gap_student,
        create_careless_student,
        create_multiple_weaknesses_student,
        create_insufficient_evidence_student
    ]
