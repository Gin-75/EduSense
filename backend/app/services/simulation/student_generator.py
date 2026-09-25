"""
Student Generator for batch simulation.
"""
from typing import List
import random
from app.services.simulation.student_profile import get_all_archetype_factories
from app.services.simulation.deterministic_student import DeterministicStudent
from app.services.simulation.llm_student import LLMStudent
from app.services.simulation.abstract_student import AbstractStudent

def generate_students(count: int, mode: str = "deterministic", seed: int = 42) -> List[AbstractStudent]:
    """
    Generates a balanced batch of students across all archetypes.
    """
    factories = get_all_archetype_factories()
    students = []
    
    rng = random.Random(seed)
    
    for i in range(count):
        factory = factories[i % len(factories)]
        profile = factory(f"student_{i:04d}")
        
        if mode == "deterministic":
            student = DeterministicStudent(profile, seed=rng.randint(0, 100000))
        elif mode == "llm":
            student = LLMStudent(profile)
        else:
            raise ValueError(f"Unknown mode: {mode}")
            
        students.append(student)
        
    return students
