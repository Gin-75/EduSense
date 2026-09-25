"""
Simulation Runner.

Orchestrates the interaction between the AbstractStudent and the real DiagnosticEngine.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.services.simulation.abstract_student import AbstractStudent
from app.services.diagnostic_engine import DiagnosticEngine
from app.services.evaluator import evaluate_math_answer, identify_error_signature
from app.models.schemas import SimulationResult
from app.models.domain import Question

class SimulationRunner:
    def __init__(self, db: Session, max_questions: int = 5):
        self.db = db
        self.engine = DiagnosticEngine(db)
        self.max_questions = max_questions

    def run_simulation(self, student: AbstractStudent) -> SimulationResult:
        """
        Runs the simulation loop.
        """
        questions_asked = []
        student_responses = []
        detected_errors = []
        
        # 1. Ask a trigger question to start the session (we need an initial error)
        initial_q = self.db.query(Question).first()
        if not initial_q:
            raise ValueError("No questions in DB")
            
        initial_response = student.respond(initial_q)
        eval_res = evaluate_math_answer(initial_q.solution, initial_response)
        
        questions_asked.append(initial_q.content)
        student_responses.append(initial_response)
        
        if eval_res["correct"]:
            # Student got the first question right. Let's try up to max_questions to find an error.
            session = None
            for i in range(self.max_questions - 1):
                next_q = self.db.query(Question).offset(i + 1).first()
                if not next_q: break
                resp = student.respond(next_q)
                e_res = evaluate_math_answer(next_q.solution, resp)
                questions_asked.append(next_q.content)
                student_responses.append(resp)
                if not e_res["correct"]:
                    err_sig = identify_error_signature(next_q.solution, resp)
                    detected_errors.append(err_sig)
                    session = self.engine.initialize_session(
                        student_id=hash(student.student_id) % 10000, 
                        initial_skill_id=1, 
                        initial_error_signature=err_sig
                    )
                    break
            
            if not session:
                return self._build_result(student, "INSUFFICIENT_EVIDENCE", 0.0, len(questions_asked), questions_asked, student_responses, detected_errors, {})
        else:
            err_sig = identify_error_signature(initial_q.solution, initial_response)
            detected_errors.append(err_sig)
            session = self.engine.initialize_session(
                student_id=hash(student.student_id) % 10000, 
                initial_skill_id=1, 
                initial_error_signature=err_sig
            )

        # 2. Adaptive Loop
        questions_used = len(questions_asked)
        
        while session.status != "completed" and questions_used < self.max_questions:
            next_q = self.engine.select_next_question(session)
            if not next_q:
                break
                
            resp = student.respond(next_q)
            e_res = evaluate_math_answer(next_q.solution, resp)
            
            questions_asked.append(next_q.content)
            student_responses.append(resp)
            questions_used += 1
            
            err_sig = None
            if not e_res["correct"]:
                err_sig = identify_error_signature(next_q.solution, resp)
                detected_errors.append(err_sig)
                
            session = self.engine.update_hypotheses(
                session, 
                question_id=next_q.id, 
                is_correct=e_res["correct"], 
                error_signature=err_sig
            )

        # 3. Finalize
        if session.status == "completed" and session.diagnosis:
            # We map engine's internal keys to our standard categories to allow comparison
            raw_diag = session.diagnosis.get("primary_cause", "")
            mapped_diag = self._map_engine_diagnosis(raw_diag)
            conf = session.confidence or 0.0
        else:
            mapped_diag = "INSUFFICIENT_EVIDENCE"
            conf = session.confidence if session else 0.0
            
        return self._build_result(student, mapped_diag, conf, questions_used, questions_asked, student_responses, detected_errors, session.hypotheses if session else {})

    def _map_engine_diagnosis(self, raw: str) -> str:
        raw_lower = raw.lower()
        if "misconception" in raw_lower: return "MISCONCEPTION"
        if "computational" in raw_lower: return "COMPUTATIONAL_ERROR"
        if "procedural" in raw_lower: return "PROCEDURAL_GAP"
        if "careless" in raw_lower: return "CARELESS_ERROR"
        return raw.upper()

    def _build_result(self, student, engine_diag, conf, q_used, q_asked, s_resp, d_err, hyp) -> SimulationResult:
        gt = student.hidden_ground_truth
        
        correct = (engine_diag == gt.category)
        
        insuf = (engine_diag == "INSUFFICIENT_EVIDENCE")
        false_diag = (not correct and not insuf and conf >= 0.4)
        
        reason = None
        if false_diag:
            reason = f"Engine diagnosed {engine_diag} but ground truth was {gt.category}"
        elif insuf and gt.category != "INSUFFICIENT_EVIDENCE":
            reason = "Engine failed to reach conclusion within budget."

        return SimulationResult(
            student_id=student.student_id,
            archetype=student.archetype,
            ground_truth=gt.model_dump(),
            engine_diagnosis=engine_diag,
            engine_confidence=conf,
            correct=correct,
            questions_used=q_used,
            false_diagnosis=false_diag,
            insufficient_evidence=insuf,
            questions_asked=q_asked,
            student_responses=s_resp,
            detected_errors=d_err,
            engine_hypotheses=hyp,
            failure_reason=reason
        )
