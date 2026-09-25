import json
from app.database import SessionLocal
from app.services.simulation.student_generator import generate_students
from app.services.simulation.simulation_runner import SimulationRunner
from app.services.simulation.baseline import StaticAssessmentEngine, ErrorFrequencyEngine
from app.services.simulation.metrics import compute_simulation_metrics
from app.services.simulation.failure_analysis import analyze_failures
from app.seed import seed_db

def main():
    print("Seeding database...")
    seed_db()
    
    db = SessionLocal()
    try:
        # Phase A: 100 students
        print("Running 100-student benchmark...")
        students = generate_students(100, mode="deterministic", seed=42)
        
        runner = SimulationRunner(db, max_questions=5)
        static_engine = StaticAssessmentEngine(db)
        freq_engine = ErrorFrequencyEngine(db)
        
        engine_results = []
        static_results = []
        freq_results = []
        
        for student in students:
            # 1. Real Engine
            engine_results.append(runner.run_simulation(student))
            
            # 2. Static Baseline
            static_diag = static_engine.run_assessment(student, 5)
            static_results.append(runner._build_result(student, static_diag["diagnosis"], static_diag["confidence"], static_diag["questions_used"], [], [], [], {}))
            
            # 3. Frequency Baseline
            freq_diag = freq_engine.run_assessment(student, 5)
            freq_results.append(runner._build_result(student, freq_diag["diagnosis"], freq_diag["confidence"], freq_diag["questions_used"], [], [], [], {}))

        engine_metrics = compute_simulation_metrics(engine_results)
        static_metrics = compute_simulation_metrics(static_results)
        freq_metrics = compute_simulation_metrics(freq_results)
        failures = analyze_failures(engine_results)
        
        print("\n--- RESULTS ---")
        print("Static Baseline Category Accuracy:", static_metrics.get("category_accuracy"))
        print("Frequency Baseline Category Accuracy:", freq_metrics.get("category_accuracy"))
        print("Engine Category Accuracy:", engine_metrics.get("category_accuracy"))
        
        print("\nEngine Metrics:")
        print(json.dumps(engine_metrics, indent=2))
        
        print(f"\n--- FAILURES ({len(failures)}) ---")
        for f in failures[:2]: # Show first 2
            print(json.dumps(f, indent=2))
            
        with open("benchmark_100_results.json", "w") as f:
            json.dump({
                "engine_metrics": engine_metrics,
                "static_metrics": static_metrics,
                "freq_metrics": freq_metrics,
                "failures": failures
            }, f, indent=2)

        # Phase B: 500 students
        print("\n\nRunning 500-student benchmark...")
        students_500 = generate_students(500, mode="deterministic", seed=99)
        engine_results_500 = [runner.run_simulation(s) for s in students_500]
        engine_metrics_500 = compute_simulation_metrics(engine_results_500)
        
        print("Engine Category Accuracy (500 runs):", engine_metrics_500.get("category_accuracy"))
        
        with open("benchmark_500_results.json", "w") as f:
            json.dump({
                "engine_metrics": engine_metrics_500
            }, f, indent=2)

    finally:
        db.close()

if __name__ == "__main__":
    main()
