"""
Failure Analysis tools.
"""
from typing import List
from app.models.schemas import SimulationResult

def analyze_failures(results: List[SimulationResult]) -> List[dict]:
    failures = []
    for r in results:
        if not r.correct:
            failures.append({
                "student_id": r.student_id,
                "archetype": r.archetype,
                "ground_truth_category": r.ground_truth.get("category"),
                "engine_diagnosis": r.engine_diagnosis,
                "engine_confidence": r.engine_confidence,
                "questions_asked": r.questions_asked,
                "student_responses": r.student_responses,
                "detected_errors": r.detected_errors,
                "engine_hypotheses": r.engine_hypotheses,
                "failure_reason": r.failure_reason
            })
    return failures
