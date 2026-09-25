"""
LLM-based Student Simulator (Mode B).
"""
from app.services.simulation.abstract_student import AbstractStudent
from app.services.simulation.student_profile import SyntheticStudentProfile
from app.models.domain import Question

class LLMStudent(AbstractStudent):
    def __init__(self, profile: SyntheticStudentProfile, provider: str = "stub"):
        super().__init__(profile)
        self.provider = provider
        
    def respond(self, question: Question) -> str:
        # For the benchmark we will predominantly use the Deterministic student.
        # This is a stub for future integration with actual LLM calls.
        return question.solution  # fallback
