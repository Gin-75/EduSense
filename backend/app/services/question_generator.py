import random
import sympy

def generate_dynamic_question(grade_level: str):
    """
    Procedurally generates a Diagnostic Multiple Choice Question (MCQ).
    Each distractor represents a specific misconception.
    """
    x = sympy.Symbol('x')
    
    if "primary" in grade_level:
        # Primary: Basic Arithmetic
        a = random.randint(11, 20)
        b = random.randint(5, 10)
        ans = a - b
        content = f"Calculate: {a} - {b}"
        skills = ["Basic Subtraction", "Number Sense"]
        
        options = [
            {"id": "A", "math": str(ans), "is_correct": True, "diagnosis": "Mastery of Basic Subtraction"},
            {"id": "B", "math": str(a + b), "is_correct": False, "diagnosis": "Wrong Operation: Added instead of Subtracted"},
            {"id": "C", "math": str(ans - 1), "is_correct": False, "diagnosis": "Off-by-one counting error"},
            {"id": "D", "math": str(a - b + 10), "is_correct": False, "diagnosis": "Tens column borrowing error"},
            {"id": "E", "math": "I don't know", "is_correct": False, "diagnosis": "Knowledge Gap (No Guessing)"}
        ]
        
        family = "arithmetic_sub"
        subject = "Arithmetic"
        
    elif "prep" in grade_level:
        # Preparatory: Linear Equations
        a = random.randint(2, 5)
        ans = random.randint(2, 7)
        b = random.randint(2, 10)
        c = a * ans + b
        
        content = f"Solve for x: {a}x + {b} = {c}"
        skills = ["Isolating Variables", "Equation Solving", "Basic Subtraction"]
        
        # Distractors
        # Mistake 1: Added b instead of subtracting
        mistake_1 = (c + b) / a
        mistake_1_str = str(int(mistake_1)) if mistake_1.is_integer() else f"{c+b}/{a}"
        
        # Mistake 2: Subtracted a instead of dividing
        mistake_2 = c - b - a
        
        # Mistake 3: Flipped signs completely
        mistake_3 = -ans
        
        options = [
            {"id": "A", "math": str(ans), "is_correct": True, "diagnosis": "Mastery of Isolating Variables"},
            {"id": "B", "math": mistake_1_str, "is_correct": False, "diagnosis": "Sign Error: Added constant to both sides instead of subtracting"},
            {"id": "C", "math": str(mistake_2), "is_correct": False, "diagnosis": "Operator Error: Subtracted coefficient instead of dividing"},
            {"id": "D", "math": str(mistake_3), "is_correct": False, "diagnosis": "Sign Flipped across equals"},
            {"id": "E", "math": "I don't know", "is_correct": False, "diagnosis": "Knowledge Gap (No Guessing)"}
        ]
        
        family = "linear_equation"
        subject = "Algebra"
        
    else:
        # Secondary: Calculus
        a = random.randint(2, 5)
        p = random.randint(2, 4)
        content = f"Differentiate with respect to x: {a}x^{p}"
        skills = ["Power Rule", "Polynomial Differentiation", "Coefficient Multiplication"]
        
        correct_ans = f"{a*p}x^{p-1}"
        mistake_1 = f"{a}x^{p-1}" # Forgot to multiply coefficient
        mistake_2 = f"{a*p}x^{p}"   # Forgot to decrement power
        mistake_3 = f"{a*p}x^{p+1}" # Incremented instead of decremented (Integration confusion)
        
        options = [
            {"id": "A", "math": correct_ans, "is_correct": True, "diagnosis": "Mastery of Power Rule"},
            {"id": "B", "math": mistake_1, "is_correct": False, "diagnosis": "Coefficient Error: Forgot to multiply power by leading coefficient"},
            {"id": "C", "math": mistake_2, "is_correct": False, "diagnosis": "Power Error: Forgot to decrement the exponent"},
            {"id": "D", "math": mistake_3, "is_correct": False, "diagnosis": "Operation Confusion: Applied Integration rule instead of Differentiation"},
            {"id": "E", "math": "I don't know", "is_correct": False, "diagnosis": "Knowledge Gap (No Guessing)"}
        ]
        
        family = "differentiation_poly"
        subject = "Calculus"

    random.shuffle(options)
    
    return {
        "content": content,
        "solution": next(opt["math"] for opt in options if opt.get("is_correct", False)),
        "options": options,
        "subject": subject,
        "structural_family": family,
        "micro_skills": skills
    }
