# True Bayesian Knowledge Tracing Engine with Unique Skill Parameters
# Solves the "identical 82% update" problem by assigning unique priors, 
# guess, and slip probabilities to every micro-skill.

# Define unique Bayesian parameters for each micro-skill
# Format: "Skill Name": {"prior": P_INIT, "guess": P_GUESS, "slip": P_SLIP}
SKILL_PARAMS = {
    # Fundamental Algebra (High Prior, Low Slip)
    "Isolating Variables": {"prior": 0.65, "guess": 0.15, "slip": 0.05},
    "Basic Addition": {"prior": 0.85, "guess": 0.10, "slip": 0.02},
    "Basic Subtraction": {"prior": 0.80, "guess": 0.10, "slip": 0.05},
    "Basic Multiplication": {"prior": 0.75, "guess": 0.15, "slip": 0.05},
    "Coefficient Division": {"prior": 0.55, "guess": 0.20, "slip": 0.10},
    "Algebraic Manipulation": {"prior": 0.50, "guess": 0.25, "slip": 0.15},
    "Equation Solving": {"prior": 0.50, "guess": 0.20, "slip": 0.10},
    "Number Sense": {"prior": 0.90, "guess": 0.10, "slip": 0.01},
    "Basic Arithmetic": {"prior": 0.90, "guess": 0.10, "slip": 0.01},
    
    # Differentiation (Medium/Low Prior, Higher Slip)
    "Power Rule": {"prior": 0.40, "guess": 0.20, "slip": 0.10},
    "Polynomial Differentiation": {"prior": 0.35, "guess": 0.20, "slip": 0.12},
    "Coefficient Multiplication": {"prior": 0.45, "guess": 0.15, "slip": 0.08},
    "Constant Rule": {"prior": 0.60, "guess": 0.10, "slip": 0.05},
    "Differentiation Addition Rule": {"prior": 0.45, "guess": 0.15, "slip": 0.10},
    "Chain Rule": {"prior": 0.15, "guess": 0.25, "slip": 0.20}, # Hard skill
    "Product Rule": {"prior": 0.20, "guess": 0.20, "slip": 0.15},
    "Trigonometric Differentiation": {"prior": 0.25, "guess": 0.15, "slip": 0.15},
    
    # Integration (Low Prior, Highest Slip)
    "Basic Integration": {"prior": 0.30, "guess": 0.20, "slip": 0.15},
    "Power Rule for Integration": {"prior": 0.25, "guess": 0.25, "slip": 0.15},
    "Coefficient Integration": {"prior": 0.35, "guess": 0.20, "slip": 0.10},
    "Trigonometric Integration": {"prior": 0.15, "guess": 0.20, "slip": 0.20},
    "Antiderivatives": {"prior": 0.20, "guess": 0.25, "slip": 0.15},
    "Sign Handling": {"prior": 0.40, "guess": 0.30, "slip": 0.25}, # Common mistake area
    "Integration by Parts": {"prior": 0.05, "guess": 0.10, "slip": 0.30}, # Very hard
    "Exponential Integration": {"prior": 0.25, "guess": 0.15, "slip": 0.10},
    
    # Fallbacks
    "Advanced Calculus": {"prior": 0.20, "guess": 0.20, "slip": 0.15},
    "Function Analysis": {"prior": 0.30, "guess": 0.25, "slip": 0.10},
}

def get_skill_params(skill: str):
    # Return specific params if they exist, else return a generic fallback
    return SKILL_PARAMS.get(skill, {"prior": 0.50, "guess": 0.20, "slip": 0.10})

# Hardcoded Micro-Skill mapping for the prototype questions
# In a full production system, this would be a database table (Q-Matrix)
QUESTION_MICRO_SKILLS = {
    # Basic Algebra
    1: ["Isolating Variables", "Basic Addition"],
    2: ["Isolating Variables", "Basic Subtraction"],
    3: ["Coefficient Division", "Isolating Variables"],
    4: ["Isolating Variables", "Basic Multiplication"],
    5: ["Isolating Variables", "Basic Subtraction"],
    10: ["Isolating Variables", "Basic Subtraction"],
    11: ["Isolating Variables", "Basic Subtraction"],
    
    # Differentiation
    21: ["Power Rule", "Polynomial Differentiation"],
    22: ["Power Rule", "Coefficient Multiplication"],
    23: ["Constant Rule", "Polynomial Differentiation"],
    24: ["Differentiation Addition Rule", "Power Rule"],
    25: ["Chain Rule", "Power Rule"],
    26: ["Product Rule", "Trigonometric Differentiation"],
    
    # Integration
    28: ["Basic Integration", "Power Rule for Integration"],
    29: ["Basic Integration", "Coefficient Integration"],
    33: ["Trigonometric Integration", "Antiderivatives"],
    34: ["Trigonometric Integration", "Sign Handling"],
    35: ["Integration by Parts", "Exponential Integration"],
}

def get_skills_for_question(question_id: int, grade_level: str) -> list:
    if question_id in QUESTION_MICRO_SKILLS:
        return QUESTION_MICRO_SKILLS[question_id]
        
    # Fallback dynamic mapping if question is not in the hardcoded list
    if "primary" in grade_level:
        return ["Basic Arithmetic", "Number Sense"]
    elif "prep" in grade_level:
        return ["Algebraic Manipulation", "Equation Solving"]
    else:
        # We also pass the question_id to the fallback so it doesn't just
        # say "Advanced Calculus" for everything.
        if (question_id % 2) == 0:
            return ["Function Analysis", "Power Rule"]
        return ["Advanced Calculus", "Antiderivatives"]

def diagnose_student_dynamic(interaction_history, grade_level="sec2"):
    """
    interaction_history: list of dicts [{'question_id': 5, 'score': 1}, ...]
    grade_level: string (e.g. 'prep1', 'sec3')
    Returns a dictionary of current micro-skill masteries (0.0 to 1.0)
    """
    
    skill_mastery = {}
    
    # Deduplicate history: keep only the latest attempt per question_id
    # This prevents the BKT algorithm from over-inflating mastery if a student retries.
    unique_interactions = {}
    for interaction in interaction_history:
        unique_interactions[interaction['question_id']] = interaction
    deduped_history = list(unique_interactions.values())
    
    latest_skills = []
    if deduped_history:
        latest_q_id = deduped_history[-1]['question_id']
        latest_skills = get_skills_for_question(latest_q_id, grade_level)
    
    # Process history chronologically using Bayesian Update
    for interaction in deduped_history:
        q_id = interaction['question_id']
        is_correct = interaction['score'] == 1
        
        req_skills = get_skills_for_question(q_id, grade_level)
        
        for skill in req_skills:
            params = get_skill_params(skill)
            
            # Initialize skill with its specific prior if not seen before
            if skill not in skill_mastery:
                skill_mastery[skill] = params["prior"]
                
            p_L = skill_mastery[skill]
            
            if is_correct:
                p_correct_given_L = 1.0 - params["slip"]
                p_correct_given_not_L = params["guess"]
                
                prob_correct = (p_correct_given_L * p_L) + (p_correct_given_not_L * (1 - p_L))
                
                if prob_correct > 0:
                    p_L_new = (p_correct_given_L * p_L) / prob_correct
                else:
                    p_L_new = p_L
            else:
                p_wrong_given_L = params["slip"]
                p_wrong_given_not_L = 1.0 - params["guess"]
                
                prob_wrong = (p_wrong_given_L * p_L) + (p_wrong_given_not_L * (1 - p_L))
                
                if prob_wrong > 0:
                    p_L_new = (p_wrong_given_L * p_L) / prob_wrong
                else:
                    p_L_new = p_L
                    
            skill_mastery[skill] = p_L_new

    return {
        "mastery_profile": skill_mastery,
        "latest_skills": latest_skills
    }
