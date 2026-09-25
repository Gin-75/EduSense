"""
Abstract Student Interface for Simulation.

Enforces strict isolation. The simulator exposes ONLY a method to answer questions.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.services.simulation.student_profile import SyntheticStudentProfile
from app.models.domain import Question

class AbstractStudent(ABC):
    def __init__(self, profile: SyntheticStudentProfile):
        self._profile = profile
        
    @property
    def student_id(self) -> str:
        return self._profile.student_id
        
    @property
    def hidden_ground_truth(self):
        """Used ONLY for post-simulation evaluation."""
        return self._profile.ground_truth
        
    @property
    def archetype(self) -> str:
        return self._profile.archetype
        
    @abstractmethod
    def respond(self, question: Question) -> str:
        """
        Generate an answer to the given question based on the hidden latent state.
        Must NOT reveal the ground truth directly.
        """
        pass
