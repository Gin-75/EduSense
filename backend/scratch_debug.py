import json
from app.database import SessionLocal
from app.services.simulation.student_generator import generate_students
from app.services.simulation.simulation_runner import SimulationRunner

def debug_students():
    db = SessionLocal()
    students = generate_students(100, mode="deterministic", seed=42)
    runner = SimulationRunner(db, max_questions=5)
    
    traces = []
    for s in students:
        res = runner.run_simulation(s)
        traces.append(res.model_dump())
        
    with open("debug_traces.json", "w") as f:
        json.dump(traces, f, indent=2)

if __name__ == "__main__":
    debug_students()
