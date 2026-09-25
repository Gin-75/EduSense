import random

class StepTrace:
    def __init__(self):
        self.steps = []
    def add_step(self, expr_before, operation, expr_after, is_valid, error_type=None):
        self.steps.append({
            "before": str(expr_before),
            "operation": operation,
            "after": str(expr_after),
            "valid": is_valid,
            "error": error_type
        })
        
class EquationSimulator:
    def __init__(self, archetype: str, seed: int):
        self.archetype = archetype
        self.rng = random.Random(seed)
        
        self.careless_rate = 0.05
        self.arithmetic_weakness_rate = 0.05
        self.procedural_gap_rate = 0.0
        
        if archetype == "Strong":
            pass
        elif archetype == "Careless":
            self.careless_rate = 0.20
        elif archetype == "Computational":
            self.arithmetic_weakness_rate = 0.40
        elif archetype == "ProceduralGap":
            self.procedural_gap_rate = 0.40
            
    def roll(self, prob):
        return self.rng.random() < prob
        
    def eval_equation(self, const1, const2) -> StepTrace:
        # x + const1 = const2
        trace = StepTrace()
        expr = f"x + {const1} = {const2}"
        
        # Step 1: Inverse Operation (Isolation)
        is_valid_op = True
        err_op = None
        op_str = f"subtract {const1}"
        
        # Valid would be: x = const2 - const1
        # Procedural gap: x = const2 + const1
        new_expr = ""
        actual_op = "sub"
        if self.roll(self.procedural_gap_rate):
            is_valid_op = False
            err_op = "wrong_operation"
            new_expr = f"x = {const2} + {const1}"
            actual_op = "add"
        elif self.roll(self.careless_rate):
            is_valid_op = False
            err_op = "careless_operation"
            new_expr = f"x = {const2} + {const1}"
            actual_op = "add"
        else:
            new_expr = f"x = {const2} - {const1}"
            
        trace.add_step(expr, "inverse_operation", new_expr, is_valid_op, err_op)
        
        # Step 2: Arithmetic Evaluation
        is_valid_arith = True
        err_arith = None
        
        correct_eval = (const2 + const1) if actual_op == "add" else (const2 - const1)
        student_eval = correct_eval
        
        if self.roll(self.arithmetic_weakness_rate):
            is_valid_arith = False
            err_arith = "arithmetic_weakness"
            # Randomly shift it, OR what if they do the opposite operation accidentally?
            # To create identical final answers: if they subtract correctly but wanted to add, it's (const2 - const1).
            # If they add incorrectly by subtracting, it's (const2 - const1).
            # Let's just simulate arithmetic drift.
            # But we want to explicitly create overlap where x=17 comes from (12-5 but bad math) and (12+5 and good math).
            # If actual_op == "sub", const2=12, const1=5. correct=7.
            # Let's say computational weakness makes them add when they see numbers:
            if actual_op == "sub":
                student_eval = const2 + const1  # x=17
            else:
                student_eval = const2 - const1
        elif self.roll(self.careless_rate):
            is_valid_arith = False
            err_arith = "careless_arithmetic"
            student_eval += self.rng.choice([-1, 1])
            
        final_expr = f"x = {student_eval}"
        trace.add_step(new_expr, "arithmetic", final_expr, is_valid_arith, err_arith)
        
        return trace

def generate_equation_dataset(num_students=500):
    archetypes = ["Strong", "Careless", "Computational", "ProceduralGap"]
    problems = [
        (5, 12),
        (3, 10),
        (7, 15),
        (2, 9),
        (4, 11)
    ] 
    
    dataset = []
    for arch in archetypes:
        for i in range(num_students):
            sim = EquationSimulator(arch, seed=hash(arch) + i)
            traces = []
            for c1, c2 in problems:
                t = sim.eval_equation(c1, c2)
                traces.append(t)
            dataset.append({
                "archetype": arch,
                "traces": [t.steps for t in traces]
            })
    return dataset
