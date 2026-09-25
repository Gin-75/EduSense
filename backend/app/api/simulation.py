"""
API layer for the Simulation Framework.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.simulation.student_generator import generate_students
from app.services.simulation.simulation_runner import SimulationRunner
from app.services.simulation.baseline import StaticAssessmentEngine, ErrorFrequencyEngine
from app.services.simulation.metrics import compute_simulation_metrics
from app.services.simulation.failure_analysis import analyze_failures
from pydantic import BaseModel

router = APIRouter(prefix="/simulation", tags=["simulation"])

class RunBatchRequest(BaseModel):
    number_of_students: int
    seed: int = 42
    mode: str = "deterministic"
    max_questions: int = 5

@router.post("/run-batch")
def run_batch(request: RunBatchRequest, db: Session = Depends(get_db)):
    students = generate_students(request.number_of_students, request.mode, request.seed)
    
    runner = SimulationRunner(db, max_questions=request.max_questions)
    static_engine = StaticAssessmentEngine(db)
    freq_engine = ErrorFrequencyEngine(db)
    
    engine_results = []
    static_results = []
    freq_results = []
    
    for student in students:
        res = runner.run_simulation(student)
        engine_results.append(res)
        
        # Baselines (just return their diagnosis for metric comparison, using the runner's result builder logic manually here for brevity)
        static_diag = static_engine.run_assessment(student, request.max_questions)
        freq_diag = freq_engine.run_assessment(student, request.max_questions)
        
        # We only really need metrics for them, but we'll pack them in the same schema
        static_results.append(runner._build_result(student, static_diag["diagnosis"], static_diag["confidence"], static_diag["questions_used"], [], [], [], {}))
        freq_results.append(runner._build_result(student, freq_diag["diagnosis"], freq_diag["confidence"], freq_diag["questions_used"], [], [], [], {}))

    return {
        "engine_metrics": compute_simulation_metrics(engine_results),
        "static_baseline_metrics": compute_simulation_metrics(static_results),
        "freq_baseline_metrics": compute_simulation_metrics(freq_results),
        "failures": analyze_failures(engine_results)
    }
