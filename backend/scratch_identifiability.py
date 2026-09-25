import json
from collections import defaultdict
from app.database import SessionLocal
from app.models.domain import Question
from app.services.simulation.student_profile import get_all_archetype_factories
from app.services.simulation.deterministic_student import DeterministicStudent
from app.services.evaluator import evaluate_math_answer, identify_error_signature

def run_analysis():
    db = SessionLocal()
    questions = db.query(Question).all()
    
    factories = get_all_archetype_factories()
    
    # matrix[archetype_name][question_id][observable_signature] = probability
    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    N_SAMPLES = 1000
    
    for factory in factories:
        arch_name = factory("test").archetype
        print(f"Sampling {arch_name}...")
        
        for i in range(N_SAMPLES):
            student = DeterministicStudent(factory(f"test_{i}"), seed=i)
            
            for q in questions:
                resp = student.respond(q)
                e_res = evaluate_math_answer(q.solution, resp)
                
                if e_res["correct"]:
                    sig = "correct"
                else:
                    sig = identify_error_signature(q.solution, resp)
                    
                matrix[arch_name][q.id][sig] += 1.0 / N_SAMPLES

    with open("identifiability_matrix.json", "w") as f:
        json.dump(matrix, f, indent=2)

if __name__ == "__main__":
    run_analysis()
