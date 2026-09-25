from app.database import engine, Base, SessionLocal
from app.models import domain, student
import json

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clean existing
    db.query(domain.QuestionMisconception).delete()
    db.query(domain.QuestionSkill).delete()
    db.query(domain.Question).delete()
    db.query(domain.Misconception).delete()
    db.query(domain.SkillDependency).delete()
    db.query(domain.Skill).delete()
    db.query(student.Student).delete()
    db.commit()
    
    # 1. Create Skills
    distributive_property = domain.Skill(name="distributive_property", subject="Algebra", difficulty=0.4)
    arithmetic = domain.Skill(name="integer_arithmetic", subject="Arithmetic", difficulty=0.2)
    sign_manipulation = domain.Skill(name="sign_manipulation", subject="Algebra", difficulty=0.3)
    linear_equations = domain.Skill(name="linear_equations", subject="Algebra", difficulty=0.5)
    inverse_operations = domain.Skill(name="inverse_operations", subject="Algebra", difficulty=0.4)
    
    db.add_all([distributive_property, arithmetic, sign_manipulation, linear_equations, inverse_operations])
    db.commit()
    
    # 2. Misconceptions
    incomplete_dist = domain.Misconception(description="incomplete_distribution", related_skill_id=distributive_property.id)
    sign_negation = domain.Misconception(description="sign_negation_error", related_skill_id=sign_manipulation.id)
    wrong_op_order = domain.Misconception(description="wrong_operation_order", related_skill_id=linear_equations.id)
    
    db.add_all([incomplete_dist, sign_negation, wrong_op_order])
    db.commit()
    
    # 3. Create ~20 Diverse Questions
    
    def add_q(content, solution, family, dp):
        q = domain.Question(
            content=content, subject="Algebra", difficulty=0.5, question_type="equation",
            solution=solution, structural_family=family, diagnostic_properties=dp
        )
        db.add(q)
        return q

    # -- Distributive Property (Standard)
    dp1 = {"tests": ["distributive_property"], "outcomes": {"incomplete_distribution": {"supports": ["MISCONCEPTION_incomplete_distribution"]}, "correct": {"weakens": ["MISCONCEPTION_incomplete_distribution", "CONCEPTUAL_GAP"]}}}
    add_q("Expand: 2*(x + 3)", "2*x + 6", "dist_positive", dp1)
    add_q("Expand: 3*(x + 5)", "3*x + 15", "dist_positive", dp1)
    add_q("Expand: 4*(x + 2)", "4*x + 8", "dist_positive", dp1)

    # -- Distributive Property (Subtraction)
    dp2 = {"tests": ["distributive_property", "sign_manipulation"], "outcomes": {"incomplete_distribution": {"supports": ["MISCONCEPTION_incomplete_distribution"]}, "sign_error": {"supports": ["MISCONCEPTION_sign_negation_error"]}, "correct": {"weakens": ["MISCONCEPTION_incomplete_distribution", "MISCONCEPTION_sign_negation_error"]}}}
    add_q("Expand: 4*(x - 2)", "4*x - 8", "dist_negative", dp2)
    add_q("Expand: 5*(x - 3)", "5*x - 15", "dist_negative", dp2)
    
    # -- Distributive Property (Negative Coefficient)
    dp3 = {"tests": ["distributive_property", "sign_manipulation"], "outcomes": {"incomplete_distribution": {"supports": ["MISCONCEPTION_incomplete_distribution"]}, "sign_error": {"supports": ["MISCONCEPTION_sign_negation_error"]}, "correct": {"weakens": ["MISCONCEPTION_incomplete_distribution", "MISCONCEPTION_sign_negation_error"]}}}
    add_q("Expand: -2*(x + 4)", "-2*x - 8", "dist_neg_coeff", dp3)
    add_q("Expand: -3*(x - 2)", "-3*x + 6", "dist_neg_coeff", dp3)

    # -- Distributive Property (Coefficient > 1 for x)
    dp4 = {"tests": ["distributive_property"], "outcomes": {"incomplete_distribution": {"supports": ["MISCONCEPTION_incomplete_distribution"]}, "correct": {"weakens": ["MISCONCEPTION_incomplete_distribution"]}}}
    add_q("Expand: 5*(2*x + 1)", "10*x + 5", "dist_coeff_x", dp4)
    add_q("Expand: 2*(3*x - 2)", "6*x - 4", "dist_coeff_x", dp4)

    # -- Linear Equations (Simple and Multi-step)
    # Likelihood tables: P(outcome | hypothesis), derived from simulator probabilities.
    # Each column sums to 1.0 for proper Bayesian updating.
    linear_eq_dp = {
        "tests": ["linear_equations", "integer_arithmetic"],
        "outcomes": {
            "correct": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.665,
                    "PROCEDURAL_GAP": 0.222,
                    "COMPUTATIONAL_ERROR": 0.222,
                    "CARELESS_ERROR": 0.258,
                    "MULTIPLE_WEAKNESSES": 0.145
                }
            },
            "arithmetic_error": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.151,
                    "PROCEDURAL_GAP": 0.051,
                    "COMPUTATIONAL_ERROR": 0.592,
                    "CARELESS_ERROR": 0.250,
                    "MULTIPLE_WEAKNESSES": 0.236
                }
            },
            "wrong_op_error": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.151,
                    "PROCEDURAL_GAP": 0.592,
                    "COMPUTATIONAL_ERROR": 0.051,
                    "CARELESS_ERROR": 0.250,
                    "MULTIPLE_WEAKNESSES": 0.236
                }
            },
            "mixed_error": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.034,
                    "PROCEDURAL_GAP": 0.135,
                    "COMPUTATIONAL_ERROR": 0.135,
                    "CARELESS_ERROR": 0.242,
                    "MULTIPLE_WEAKNESSES": 0.383
                }
            }
        }
    }
    add_q("Solve: x + 5 = 12", "7", "lin_eq_add", linear_eq_dp)
    add_q("Solve: x + 7 = 15", "8", "lin_eq_add", linear_eq_dp)
    add_q("Solve: x - 3 = 10", "13", "lin_eq_sub", linear_eq_dp)
    add_q("Solve: 2*x + 3 = 11", "4", "lin_eq_mult", linear_eq_dp)
    add_q("Solve: 3*x + 5 = 20", "5", "lin_eq_mult", linear_eq_dp)
    add_q("Solve: 4*x - 2 = 14", "4", "lin_eq_mult", linear_eq_dp)

    # -- Sign Handling (Pure arithmetic)
    dp7 = {"tests": ["sign_manipulation", "integer_arithmetic"], "outcomes": {"sign_error": {"supports": ["MISCONCEPTION_sign_negation_error"]}, "correct": {"weakens": ["MISCONCEPTION_sign_negation_error"]}}}
    add_q("Simplify: 5 - (-3)", "8", "sign_sub_neg", dp7)
    add_q("Simplify: 10 - (-2)", "12", "sign_sub_neg", dp7)
    add_q("Simplify: -4 - (-4)", "0", "sign_sub_neg", dp7)
    add_q("Simplify: -5 + 3", "-2", "sign_add", dp7)
    add_q("Simplify: -7 - 2", "-9", "sign_add", dp7)
    
    db.commit()
    
    # -- Calculus Skills and Misconceptions
    differentiation = domain.Skill(name="differentiation", subject="Calculus", difficulty=0.6)
    integration = domain.Skill(name="integration", subject="Calculus", difficulty=0.7)
    db.add_all([differentiation, integration])
    db.commit()

    power_rule_err = domain.Misconception(description="power_rule_error", related_skill_id=differentiation.id)
    chain_rule_err = domain.Misconception(description="chain_rule_error", related_skill_id=differentiation.id)
    integration_c_err = domain.Misconception(description="missing_constant_c", related_skill_id=integration.id)
    db.add_all([power_rule_err, chain_rule_err, integration_c_err])
    db.commit()

    # -- Calculus Questions
    # Define likelihoods for calculus questions
    calc_dp = {
        "tests": ["differentiation", "integration"],
        "outcomes": {
            "correct": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.6,
                    "MISCONCEPTION_power_rule": 0.1,
                    "MISCONCEPTION_chain_rule": 0.1,
                    "MISCONCEPTION_integration_c": 0.1,
                    "PROCEDURAL_GAP": 0.2,
                    "COMPUTATIONAL_ERROR": 0.3,
                    "CARELESS_ERROR": 0.4,
                    "MULTIPLE_WEAKNESSES": 0.1
                }
            },
            "wrong_op_error": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.1,
                    "MISCONCEPTION_power_rule": 0.4,
                    "MISCONCEPTION_chain_rule": 0.4,
                    "MISCONCEPTION_integration_c": 0.1,
                    "PROCEDURAL_GAP": 0.3,
                    "COMPUTATIONAL_ERROR": 0.1,
                    "CARELESS_ERROR": 0.2,
                    "MULTIPLE_WEAKNESSES": 0.3
                }
            },
            "missing_c_error": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.1,
                    "MISCONCEPTION_power_rule": 0.1,
                    "MISCONCEPTION_chain_rule": 0.1,
                    "MISCONCEPTION_integration_c": 0.7,
                    "PROCEDURAL_GAP": 0.1,
                    "COMPUTATIONAL_ERROR": 0.1,
                    "CARELESS_ERROR": 0.3,
                    "MULTIPLE_WEAKNESSES": 0.3
                }
            },
            "arithmetic_error": {
                "likelihoods": {
                    "NO_SIGNIFICANT_WEAKNESS": 0.1,
                    "MISCONCEPTION_power_rule": 0.1,
                    "MISCONCEPTION_chain_rule": 0.1,
                    "MISCONCEPTION_integration_c": 0.1,
                    "PROCEDURAL_GAP": 0.1,
                    "COMPUTATIONAL_ERROR": 0.6,
                    "CARELESS_ERROR": 0.3,
                    "MULTIPLE_WEAKNESSES": 0.3
                }
            }
        }
    }

    # Differentiation Power Rule
    add_q("Differentiate: x**2", "2*x", "calc_diff_power", calc_dp)
    add_q("Differentiate: 3*x**3", "9*x**2", "calc_diff_power", calc_dp)
    add_q("Differentiate: 5*x**4", "20*x**3", "calc_diff_power", calc_dp)
    add_q("Differentiate: x**5 + 2*x", "5*x**4 + 2", "calc_diff_power", calc_dp)

    # Differentiation Chain Rule
    add_q("Differentiate: (x + 1)**2", "2*(x + 1)", "calc_diff_chain", calc_dp)
    add_q("Differentiate: (2*x + 3)**2", "4*(2*x + 3)", "calc_diff_chain", calc_dp)
    add_q("Differentiate: sin(2*x)", "2*cos(2*x)", "calc_diff_chain", calc_dp)
    add_q("Differentiate: exp(3*x)", "3*exp(3*x)", "calc_diff_chain", calc_dp)

    # Integration Power Rule
    add_q("Integrate: 2*x", "x**2 + C", "calc_int_power", calc_dp)
    add_q("Integrate: 3*x**2", "x**3 + C", "calc_int_power", calc_dp)
    add_q("Integrate: 4*x**3", "x**4 + C", "calc_int_power", calc_dp)
    add_q("Integrate: x", "x**2/2 + C", "calc_int_power", calc_dp)

    # Integration Basic Trig
    add_q("Integrate: cos(x)", "sin(x) + C", "calc_int_trig", calc_dp)
    add_q("Integrate: -sin(x)", "cos(x) + C", "calc_int_trig", calc_dp)
    add_q("Integrate: exp(x)", "exp(x) + C", "calc_int_trig", calc_dp)

    # -- Advanced Calculus (V2) --
    adv_integration = domain.Skill(name="integration_by_parts", subject="Calculus", difficulty=0.9)
    adv_differentiation = domain.Skill(name="implicit_differentiation", subject="Calculus", difficulty=0.8)
    db.add_all([adv_integration, adv_differentiation])
    db.commit()

    parts_err = domain.Misconception(description="parts_formula_error", related_skill_id=adv_integration.id)
    implicit_err = domain.Misconception(description="implicit_chain_rule_error", related_skill_id=adv_differentiation.id)
    db.add_all([parts_err, implicit_err])
    db.commit()

    # Integration by Parts
    # Note: These are advanced so they have heavy procedural gap likelihoods.
    add_q("Integrate: x*exp(x)", "x*exp(x) - exp(x) + C", "calc_int_parts", calc_dp)
    add_q("Integrate: x*sin(x)", "-x*cos(x) + sin(x) + C", "calc_int_parts", calc_dp)
    add_q("Integrate: ln(x)", "x*ln(x) - x + C", "calc_int_parts", calc_dp)

    db.commit()
    
    # 6. Dummy Student
    test_student = student.Student(username="test_student_1")
    db.add(test_student)
    db.commit()
    
    print("Database successfully seeded with 20 diverse diagnostic questions!")
    db.close()

if __name__ == "__main__":
    seed_db()
