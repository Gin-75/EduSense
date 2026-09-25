import json
import math
from collections import defaultdict
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

from app.database import SessionLocal
from app.models.domain import Question
from app.services.simulation.student_profile import get_all_archetype_factories
from app.services.simulation.deterministic_student import DeterministicStudent

def compute_ast_signature(expected: str, student: str) -> str:
    transformations = standard_transformations + (implicit_multiplication_application,)
    try:
        expected_expr = parse_expr(expected, transformations=transformations)
        student_expr = parse_expr(student, transformations=transformations)
        diff = sympy.simplify(student_expr - expected_expr)
        
        if diff == 0:
            return "correct"
            
        # Level 2 features:
        if diff.is_constant():
            return "constant_error"
            
        if diff.has(sympy.Symbol('x')):
            # is it a coefficient error?
            x = sympy.Symbol('x')
            if diff.diff(x).is_constant() and diff.subs(x, 0) == 0:
                return "coefficient_error"
            # sign error on x?
            if expected_expr.has(x) and student_expr.has(x):
                # e.g., expected 3x, student -3x -> diff -6x
                return "x_term_error"
                
        return "complex_ast_error"
    except Exception:
        return "unparseable"

def run_level2_analysis():
    db = SessionLocal()
    questions = db.query(Question).all()
    factories = get_all_archetype_factories()
    
    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    N_SAMPLES = 500
    
    for factory in factories:
        arch_name = factory("test").archetype
        print(f"Sampling Level 2 AST for {arch_name}...")
        
        for i in range(N_SAMPLES):
            student = DeterministicStudent(factory(f"test_{i}"), seed=i)
            
            for q in questions:
                resp = student.respond(q)
                sig = compute_ast_signature(q.solution, resp)
                matrix[arch_name][q.id][sig] += 1.0 / N_SAMPLES

    with open("identifiability_matrix_level2.json", "w") as f:
        json.dump(matrix, f, indent=2)

if __name__ == "__main__":
    run_level2_analysis()
