"""
Deterministic Mode A Student Simulator.

Generates reproducible responses based on a seed and the latent skill mastery.
"""

import random
import re
from typing import Optional
from app.services.simulation.abstract_student import AbstractStudent
from app.services.simulation.student_profile import SyntheticStudentProfile
from app.models.domain import Question


class DeterministicStudent(AbstractStudent):
    def __init__(self, profile: SyntheticStudentProfile, seed: int = 42):
        super().__init__(profile)
        self.rng = random.Random(f"{profile.student_id}_{seed}")

    def respond(self, question: Question) -> str:
        """
        Produce a deterministic response.
        1. Check if the question triggers a known misconception.
        2. If not, check if they fail due to skill mastery.
        3. If not, check for careless error.
        4. Otherwise, return correct answer.
        """
        # Determine relevant skills for this question (mock logic, ideally read from question mapping)
        # We will parse the question content to guess the skill if not linked.
        q_text = question.content.lower()
        skills = []
        if "(" in q_text and ")" in q_text:
            skills.append("distributive_property")
        if "=" in q_text:
            skills.append("linear_equations")
        if "+" in q_text or "-" in q_text:
            skills.append("integer_arithmetic")

        # 1. Check for specific misconceptions
        if "incomplete_distribution" in self._profile.misconceptions and "distributive_property" in skills:
            # They have the misconception, do they apply it? Usually yes, but probabilistic.
            if self.rng.random() < 0.9:  # Misconceptions are consistently applied
                return self._apply_incomplete_distribution(question.content)
                
        if "sign_negation_error" in self._profile.misconceptions and "-" in q_text:
             if self.rng.random() < 0.9:
                 return self._apply_sign_error(question.content, question.solution)

        if "wrong_operation_order" in self._profile.misconceptions and "linear_equations" in skills:
             if self.rng.random() < 0.9:
                 return self._apply_wrong_operation(question.content)

        # 2. Check skill mastery gaps
        for skill in skills:
            mastery = self._profile.skill_mastery.get(skill, 0.5)
            if self.rng.random() > mastery:
                # Skill failure
                return self._generate_generic_wrong_answer(question.solution)

        # 3. Careless error
        if self.rng.random() < self._profile.behavior.careless_error_rate:
            return self._generate_generic_wrong_answer(question.solution)

        # 4. Correct answer
        return question.solution

    def _apply_incomplete_distribution(self, q_text: str) -> str:
        """Transforms 'a(bx + c)' to 'abx + c'"""
        # Ex: "2*(x + 3)" -> "2*x + 3"
        # Ex: "4*(x - 2)" -> "4*x - 2"
        match = re.search(r'(\d+)\*\s*\(\s*([a-zA-Z]+)\s*([+-])\s*(\d+)\s*\)', q_text)
        if match:
            coeff, var, sign, const = match.groups()
            return f"{coeff}*{var} {sign} {const}"
            
        # Fallback if format is different
        return "WRONG_INCOMPLETE_DIST"
        
    def _apply_sign_error(self, q_text: str, expected: str) -> str:
        return "SIGN_ERROR"

    def _apply_wrong_operation(self, q_text: str) -> str:
        return "WRONG_OP_ERROR"

    def _generate_generic_wrong_answer(self, expected: str) -> str:
        # Just mutate the answer slightly
        try:
            val = float(expected)
            return str(val + self.rng.randint(1, 5))
        except:
            if "x" in expected:
                return expected.replace("x", "x + 1")
            return "WRONG_ANSWER"

