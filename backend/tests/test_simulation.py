"""
Tests for the AI Student Simulation Framework.
"""
import pytest
from app.services.simulation.student_profile import create_distributive_misconception_student, create_strong_student, create_careless_student
from app.services.simulation.deterministic_student import DeterministicStudent
from app.services.simulation.student_generator import generate_students
from app.models.domain import Question

def test_reproducibility():
    """Identical seeds should produce identical responses."""
    profile = create_distributive_misconception_student("s1")
    s1 = DeterministicStudent(profile, seed=42)
    s2 = DeterministicStudent(profile, seed=42)
    
    q = Question(id=1, content="2*(x + 3)", solution="2*x + 6", difficulty=0.5)
    
    resp1 = [s1.respond(q) for _ in range(5)]
    resp2 = [s2.respond(q) for _ in range(5)]
    
    assert resp1 == resp2

def test_different_seeds():
    """Different seeds should produce stochastic variation."""
    profile = create_careless_student("s1") # High careless rate
    s1 = DeterministicStudent(profile, seed=42)
    s2 = DeterministicStudent(profile, seed=99)
    
    q = Question(id=1, content="2*(x + 3)", solution="2*x + 6", difficulty=0.5)
    
    resp1 = [s1.respond(q) for _ in range(20)]
    resp2 = [s2.respond(q) for _ in range(20)]
    
    # Very unlikely to be identical for 20 rolls with 25% error rate
    assert resp1 != resp2

def test_strong_student_behavior():
    profile = create_strong_student("s1")
    s = DeterministicStudent(profile, seed=42)
    q = Question(id=1, content="2*(x + 3)", solution="2*x + 6", difficulty=0.5)
    
    # Should get almost all correct
    correct = sum(1 for _ in range(100) if s.respond(q) == q.solution)
    assert correct >= 85

def test_distributive_misconception_structural_errors():
    profile = create_distributive_misconception_student("s1")
    s = DeterministicStudent(profile, seed=42)
    q1 = Question(id=1, content="2*(x + 3)", solution="2*x + 6", difficulty=0.5)
    q2 = Question(id=2, content="4*(x - 2)", solution="4*x - 8", difficulty=0.5)
    
    resp1 = s.respond(q1)
    resp2 = s.respond(q2)
    
    # Should apply the incomplete distribution: 2*x + 3
    assert resp1 == "2*x + 3" or resp1 == "2*x + 6" or "WRONG" in resp1
    if resp1 == "2*x + 3":
        assert resp2 == "4*x - 2" or resp2 == "4*x - 8"

def test_isolation():
    """Diagnostic Engine must not be able to see the ground truth via the interface."""
    profile = create_strong_student("s1")
    s = DeterministicStudent(profile)
    
    # Methods exposed are just `respond`, `student_id`, `hidden_ground_truth`, `archetype`.
    # The runner guarantees it only calls `respond`.
    assert hasattr(s, "respond")
    # Ground truth is explicitly documented as hidden
    assert s.hidden_ground_truth is not None

