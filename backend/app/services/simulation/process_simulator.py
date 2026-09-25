import random
from typing import List

class ProbabilisticProcessSimulator:
    def __init__(self, archetype: str, seed: int):
        self.rng = random.Random(seed)
        self.archetype = archetype
        
        # Latent probabilistic behavioral model
        self.p_careless = 0.05
        self.p_computational = 0.05
        self.p_procedural = 0.05
        
        if archetype == "Strong":
            pass
        elif archetype == "Careless":
            self.p_careless = 0.25
        elif archetype == "Computational":
            self.p_computational = 0.45
        elif archetype == "ProceduralGap":
            self.p_procedural = 0.45
        elif archetype == "Multiple":
            self.p_computational = 0.35
            self.p_procedural = 0.35

    def roll(self, prob: float) -> bool:
        return self.rng.random() < prob

    def generate_linear_equation_work(self, a: int, b: int, c: int) -> List[str]:
        """
        Generates step-by-step work for equation: a*x + b = c
        """
        steps = []
        current_expr = f"{a}*x + {b} = {c}"
        steps.append(current_expr)
        
        # Step 1: Isolate term (Transformation)
        # Valid: subtract b
        # Invalid procedural: add b, divide b, etc.
        # Careless: isolated random slip in operation
        
        op_choice = "valid"
        if self.roll(self.p_procedural):
            # Systematically wrong operation logic
            op_choice = self.rng.choice(["add_b", "subtract_c"])
        elif self.roll(self.p_careless):
            # Random careless slip
            op_choice = self.rng.choice(["add_b"])
            
        if op_choice == "valid":
            step1_expr = f"{a}*x = {c} - {b}"
            rhs_expr_type = "sub"
        elif op_choice == "add_b":
            step1_expr = f"{a}*x = {c} + {b}"
            rhs_expr_type = "add"
        elif op_choice == "subtract_c":
            step1_expr = f"{a}*x = {b} - {c}"
            rhs_expr_type = "sub_rev"
            
        steps.append(step1_expr)
        
        # Step 2: Arithmetic Evaluation
        arith_correct = True
        if self.roll(self.p_computational):
            arith_correct = False
        elif self.roll(self.p_careless):
            arith_correct = False
            
        if rhs_expr_type == "sub":
            correct_val = c - b
        elif rhs_expr_type == "add":
            correct_val = c + b
        elif rhs_expr_type == "sub_rev":
            correct_val = b - c
            
        if arith_correct:
            step2_expr = f"{a}*x = {correct_val}"
            final_rhs = correct_val
        else:
            # Arithmetic failure
            offset = self.rng.choice([-2, -1, 1, 2])
            step2_expr = f"{a}*x = {correct_val + offset}"
            final_rhs = correct_val + offset
            
        steps.append(step2_expr)
        
        # Step 3: Division
        # Valid: divide by a
        div_choice = "valid"
        if self.roll(self.p_procedural):
            div_choice = self.rng.choice(["multiply_a", "subtract_a"])
        elif self.roll(self.p_careless):
            div_choice = self.rng.choice(["multiply_a"])
            
        if div_choice == "valid":
            step3_expr = f"x = {final_rhs}/{a}"
            div_type = "div"
        elif div_choice == "multiply_a":
            step3_expr = f"x = {final_rhs}*{a}"
            div_type = "mul"
        elif div_choice == "subtract_a":
            step3_expr = f"x = {final_rhs} - {a}"
            div_type = "sub"
            
        steps.append(step3_expr)
        
        # Step 4: Final Arithmetic (if integer div, we evaluate)
        # Just evaluating the fraction or product
        arith_correct2 = True
        if self.roll(self.p_computational):
            arith_correct2 = False
        elif self.roll(self.p_careless):
            arith_correct2 = False
            
        if div_type == "div":
            # For simplicity in simulation, keep as float or round
            val = round(final_rhs / a, 2)
        elif div_type == "mul":
            val = final_rhs * a
        elif div_type == "sub":
            val = final_rhs - a
            
        if not arith_correct2:
            val += self.rng.choice([-1.0, 1.0])
            
        steps.append(f"x = {val}")
        
        return steps

