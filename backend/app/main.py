from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import domain, student
from app.models import evaluation as evaluation_model  # noqa: F401 — registers table
from app.services.evaluator import evaluate_math_answer, identify_error_signature
from app.services.diagnostic_engine import DiagnosticEngine
from app.api.evaluation import router as evaluation_router
from app.api.simulation import router as simulation_router
from pydantic import BaseModel

# Create database tables (includes evaluation_results)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Adaptive Diagnostic Assessment Engine")

# Mount the independent evaluator API
app.include_router(evaluation_router)
app.include_router(simulation_router)

from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from app.services.cdm_inference import diagnose_student_dynamic

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas for API
class AnswerSubmission(BaseModel):
    student_id: int
    question_id: int
    answer: str

class AssessmentResponse(BaseModel):
    correct: bool
    diagnostic_session_id: int | None = None
    next_question_id: int | None = None
    message: str | None = None
    diagnosis: dict | None = None

class ProcessSubmission(BaseModel):
    student_id: int
    question_id: int
    trace: List[str]
    grade_level: Optional[str] = "sec2"

class QuestionResponse(BaseModel):
    id: int
    content: str
    solution: str
    options: Optional[List[Dict[str, Any]]] = None

class ProcessResponse(BaseModel):
    status: str
    next_question: Optional[QuestionResponse] = None
    diagnosis: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    message: Optional[str] = None

@app.get("/subjects", response_model=List[str])
def get_subjects(db: Session = Depends(get_db)):
    subjects = db.query(domain.Question.subject).distinct().all()
    return sorted([s[0] for s in subjects if s[0]])

@app.get("/start_session", response_model=QuestionResponse)
def start_session(subject: str = None, db: Session = Depends(get_db)):
    """Start a new session and get a question, filtered by subject."""
    import random
    
    query = db.query(domain.Question)
    if subject and subject != 'all':
        query = query.filter(domain.Question.subject == subject)
            
    questions = query.all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this subject")
        
    question = random.choice(questions)
    return QuestionResponse(id=question.id, content=question.content, solution=question.solution, options=question.options)

from app.services.process_evaluator import evaluate_process
def categorize_process_evidence(observations: list) -> str:
    # ... legacy evaluator function
    return "correct"

@app.post("/submit_process", response_model=ProcessResponse)
def submit_process(submission: ProcessSubmission, db: Session = Depends(get_db)):
    """Evaluate a step-by-step process."""
    question = db.query(domain.Question).filter(domain.Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # If it's a multiple choice submission, the user will just pass the option ID or math text in trace
    student_answer_raw = submission.trace[-1] if submission.trace else ""
    
    # Check if the question has options
    if question.options:
        # It's an MCQ
        selected_opt = next((o for o in question.options if o["math"] == student_answer_raw), None)
        if selected_opt:
            is_correct = selected_opt.get("is_correct", False)
            primary_cause = selected_opt.get("diagnosis", "Unknown Error")
        else:
            is_correct = False
            primary_cause = "Invalid Selection"
            
        outcome = "correct" if is_correct else "incorrect"
        
        if outcome == "correct":
            report = "Great job! Your selection is correct."
            primary_cause = "No Significant Weakness"
        else:
            if primary_cause == "Knowledge Gap (No Guessing)":
                report = "It's completely okay to not know! We will adjust your level and try an easier concept."
            elif primary_cause in ["Unknown Error", "Invalid Selection"]:
                from app.services.llm_analyzer import analyze_student_error_llm
                llm_feedback = analyze_student_error_llm(
                    question_content=question.content,
                    expected_solution=question.solution,
                    student_trace=[student_answer_raw],
                    subject=question.subject,
                    construct=question.structural_family
                )
                primary_cause = llm_feedback["primary_cause"]
                report = llm_feedback["report"]
            else:
                report = f"You fell into a common trap: {primary_cause}. Don't worry, this helps us pinpoint your exact needs."
    else:
        # Fallback to legacy process evaluator if no options
        observations = evaluate_process(submission.trace)
        outcome = categorize_process_evidence(observations)
        if outcome == "correct":
            primary_cause = "No Significant Weakness"
            report = "Great job! Your step-by-step logic is correct."
        else:
            from app.services.llm_analyzer import analyze_student_error_llm
            llm_feedback = analyze_student_error_llm(
                question_content=question.content,
                expected_solution=question.solution,
                student_trace=submission.trace,
                subject=question.subject,
                construct=question.structural_family
            )
            primary_cause = llm_feedback["primary_cause"]
            report = llm_feedback["report"]

    # --- EduCDM NCDM Integration via Database ---
    score_val = 1.0 if outcome == "correct" else 0.0
    attempt = student.Attempt(
        student_id=submission.student_id,
        question_id=submission.question_id,
        answer=student_answer_raw,
        parsed_work=submission.trace,
        correctness=score_val,
        error_signature=primary_cause
    )
    db.add(attempt)
    db.commit()
    
    student_attempts = db.query(student.Attempt).filter(
        student.Attempt.student_id == submission.student_id
    ).order_by(student.Attempt.timestamp.asc()).all()
    
    interaction_history = [
        {'question_id': att.question_id, 'score': 1 if att.correctness >= 1.0 else 0} 
        for att in student_attempts
    ]
    
    ncdm_mastery = diagnose_student_dynamic(interaction_history, grade_level=submission.grade_level)
    
    diag_payload = {
        "primary_cause": primary_cause,
        "report": report,
        "ncdm_mastery": ncdm_mastery
    }
    
    # Session length rule: end session if they've answered 10 questions
    is_completed = len(student_attempts) >= 10
    
    if is_completed:
        return ProcessResponse(
            status="completed",
            diagnosis=diag_payload,
            message="Diagnostic complete."
        )

    # Pick next question from the same subject
    import random
    subject = question.subject
    next_questions = db.query(domain.Question).filter(
        domain.Question.subject == subject,
        domain.Question.id != question.id
    ).all()
    
    if next_questions:
        next_q = random.choice(next_questions)
    else:
        # Fallback to any random question if it's the only one in the subject
        next_q = db.query(domain.Question).filter(domain.Question.id != question.id).first()

    return ProcessResponse(
        status="active",
        next_question=QuestionResponse(id=next_q.id, content=next_q.content, solution=next_q.solution, options=next_q.options),
        diagnosis=diag_payload,
        message="Please solve the next problem."
    )

@app.post("/submit_answer", response_model=AssessmentResponse)
def submit_answer(submission: AnswerSubmission, db: Session = Depends(get_db)):
    """
    Endpoint to process a student's answer.
    """
    # Fetch question
    question = db.query(domain.Question).filter(domain.Question.id == submission.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Evaluate answer
    eval_result = evaluate_math_answer(question.solution, submission.answer)
    
    # Record attempt
    error_signature = None
    if not eval_result["correct"]:
        error_signature = identify_error_signature(question.solution, submission.answer)
        
    attempt = student.Attempt(
        student_id=submission.student_id,
        question_id=submission.question_id,
        answer=submission.answer,
        correctness=1.0 if eval_result["correct"] else 0.0,
        error_signature=error_signature
    )
    db.add(attempt)
    db.commit()
    
    if eval_result["correct"]:
        return AssessmentResponse(
            correct=True,
            message="Correct answer!"
        )
        
    # Incorrect Answer -> Trigger Diagnostic Engine
    engine_svc = DiagnosticEngine(db)
    
    # Check if there is an active session for this student (stub logic)
    active_session = db.query(student.DiagnosticSession).filter(
        student.DiagnosticSession.student_id == submission.student_id,
        student.DiagnosticSession.status == "active"
    ).first()
    
    if not active_session:
        # Start new diagnostic session
        # Assume question is linked to some skill (stub skill ID 1)
        active_session = engine_svc.initialize_session(submission.student_id, initial_skill_id=1, initial_evidence=error_signature, initial_question_id=submission.question_id)
    else:
        # Update existing session
        active_session = engine_svc.process_answer(active_session, submission.question_id, error_signature or "unknown")
        
    if active_session.status == "completed":
        return AssessmentResponse(
            correct=False,
            message="Diagnostic complete.",
            diagnosis=active_session.diagnosis
        )
        
    # Select next question
    next_q = engine_svc.select_next_question(active_session)
    
    return AssessmentResponse(
        correct=False,
        diagnostic_session_id=active_session.id,
        next_question_id=next_q.id if next_q else None,
        message="Let's try to understand what went wrong."
    )

@app.get("/health")
def health_check():
    return {"status": "ok"}
