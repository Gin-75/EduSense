"""
Baseline diagnostic strategies for comparison.
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.domain import Question
from app.services.simulation.abstract_student import AbstractStudent

class BaselineEngine:
    def __init__(self, db: Session):
        self.db = db

class StaticAssessmentEngine(BaselineEngine):
    """
    Baseline #1: Static Skill Assessment Baseline
    Asks a fixed sequence of questions (max_questions).
    Diagnoses based on whichever skill had the most failures.
    """
    def run_assessment(self, student: AbstractStudent, max_questions: int = 5) -> Dict[str, Any]:
        questions = self.db.query(Question).limit(max_questions).all()
        if not questions:
            return {"diagnosis": "INSUFFICIENT_EVIDENCE", "confidence": 0.0, "questions_used": 0}
            
        failures = 0
        for q in questions:
            resp = student.respond(q)
            # Basic check
            # In a real static assessment, we'd check if resp is correct
            # For simplicity, we just check against q.solution using exact string match or simplified logic
            if resp.replace(" ", "") != q.solution.replace(" ", ""):
                failures += 1
                
        # If failures > threshold, guess misconception, else careless
        if failures >= 2:
            diag = "MISCONCEPTION"
        elif failures == 1:
             diag = "CARELESS_ERROR"
        else:
             diag = "INSUFFICIENT_EVIDENCE"
             
        return {
            "diagnosis": diag,
            "confidence": min(1.0, failures / max_questions),
            "questions_used": len(questions)
        }

class ErrorFrequencyEngine(BaselineEngine):
    """
    Baseline #2: Error-Frequency Baseline
    No adaptive questioning. Just counts error types over a fixed set.
    """
    def run_assessment(self, student: AbstractStudent, max_questions: int = 5) -> Dict[str, Any]:
        questions = self.db.query(Question).limit(max_questions).all()
        error_counts = {}
        
        for q in questions:
            resp = student.respond(q)
            resp_clean = resp.replace(" ", "")
            sol_clean = q.solution.replace(" ", "")
            
            if resp_clean != sol_clean:
                # Stub heuristic for error sig
                if "2*x+3" in resp_clean or "4*x-2" in resp_clean:
                    err = "incomplete_distribution"
                else:
                    err = "unknown"
                error_counts[err] = error_counts.get(err, 0) + 1
                
        if not error_counts:
            return {"diagnosis": "INSUFFICIENT_EVIDENCE", "confidence": 0.0, "questions_used": len(questions)}
            
        most_frequent = max(error_counts.items(), key=lambda x: x[1])
        if most_frequent[1] >= 2:
            return {"diagnosis": "MISCONCEPTION", "confidence": most_frequent[1]/len(questions), "questions_used": len(questions)}
        return {"diagnosis": "COMPUTATIONAL_ERROR", "confidence": 0.4, "questions_used": len(questions)}

