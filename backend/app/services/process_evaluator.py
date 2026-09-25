import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy.parsing.latex import parse_latex

def evaluate_process(student_steps: list[str]) -> list[dict]:
    """
    Evaluates a sequence of mathematical steps.
    Returns a list of observations. It DOES NOT classify cause.
    It purely observes mathematical equivalence and structural difference.
    """
    transformations = standard_transformations + (implicit_multiplication_application,)
    observations = []
    
    for i in range(1, len(student_steps)):
        prev_str = student_steps[i-1]
        curr_str = student_steps[i]
        
        obs = {
            "step_index": i,
            "previous": prev_str,
            "current": curr_str,
            "equivalent": False,
            "operation_class": "unknown",
            "parsing_error": False
        }
        
        try:
            def parse_any(expr_str):
                expr_str = expr_str.strip()
                parsed = None
                try:
                    # If it has backslashes or carets, it's likely LaTeX
                    if '\\' in expr_str or '^' in expr_str:
                        parsed = parse_latex(expr_str)
                except Exception:
                    pass
                
                if parsed is None:
                    # Fallback
                    parsed = parse_expr(expr_str, transformations=transformations)
                return parsed
                        
            # Handle Equations vs Expressions
            is_prev_eq = "=" in prev_str
            is_curr_eq = "=" in curr_str
            
            if is_prev_eq and is_curr_eq:
                p_left, p_right = prev_str.split("=")
                c_left, c_right = curr_str.split("=")
                
                pl_expr = parse_any(p_left)
                pr_expr = parse_any(p_right)
                cl_expr = parse_any(c_left)
                cr_expr = parse_any(c_right)
                
                diff_prev = sympy.simplify(pl_expr - pr_expr)
                diff_curr = sympy.simplify(cl_expr - cr_expr)
                
                # They are equivalent if diff_prev = k * diff_curr
                try:
                    ratio = sympy.simplify(diff_prev / diff_curr)
                    obs["equivalent"] = ratio.is_constant() and ratio != 0
                except:
                    obs["equivalent"] = False
                
                # Classify the mathematical observation (not the cause)
                if sympy.simplify(pl_expr - cl_expr) == 0:
                    if sympy.simplify(pr_expr - cr_expr).is_constant():
                         obs["operation_class"] = "arithmetic"
                    else:
                         obs["operation_class"] = "algebraic_simplification"
                elif sympy.simplify(pr_expr - cr_expr) == 0:
                    if sympy.simplify(pl_expr - cl_expr).is_constant():
                         obs["operation_class"] = "arithmetic"
                    else:
                         obs["operation_class"] = "algebraic_simplification"
                else:
                    if obs["equivalent"]:
                        obs["operation_class"] = "valid_operation"
                    else:
                        obs["operation_class"] = "invalid_operation"
                        
            elif not is_prev_eq and not is_curr_eq:
                # Expressions (including calculus)
                def preprocess_expr(expr_str):
                    expr_str = expr_str.strip()
                    if expr_str.startswith("Differentiate:"):
                        inner = expr_str.replace("Differentiate:", "").strip()
                        parsed = parse_any(inner)
                        x = sympy.Symbol('x')
                        return sympy.diff(parsed, x)
                    elif expr_str.startswith("Integrate:"):
                        inner = expr_str.replace("Integrate:", "").strip()
                        parsed = parse_any(inner)
                        x = sympy.Symbol('x')
                        return sympy.integrate(parsed, x)
                    return parse_any(expr_str)

                prev_expr = preprocess_expr(prev_str)
                curr_expr = preprocess_expr(curr_str)
                
                # Check for + C in integration
                C = sympy.Symbol('C')
                
                difference = sympy.simplify(prev_expr - curr_expr)
                
                if difference == 0:
                    obs["equivalent"] = True
                elif difference == C or difference == -C:
                    obs["equivalent"] = False
                    obs["operation_class"] = "missing_c_error"
                else:
                    obs["equivalent"] = False

                if not obs["equivalent"] and obs["operation_class"] == "unknown":
                    if difference.is_constant() and not difference.has(C):
                        obs["operation_class"] = "arithmetic"
                    else:
                        # Advanced V2: AST Diffing Heuristics
                        if hasattr(prev_expr, 'args') and hasattr(curr_expr, 'args'):
                            # 1. Sign Flipped: Check absolute terms match securely
                            if prev_expr.func == sympy.Add and curr_expr.func == sympy.Add:
                                if len(prev_expr.args) == len(curr_expr.args):
                                    prev_terms = {abs(t) for t in prev_expr.args}
                                    curr_terms = {abs(t) for t in curr_expr.args}
                                    if prev_terms == curr_terms:
                                        obs["operation_class"] = "sign_flipped_error"
                                    else:
                                        obs["operation_class"] = "algebraic_mutation"
                                else:
                                    obs["operation_class"] = "algebraic_mutation"
                            # 2. Power Dropped
                            elif prev_expr.func == sympy.Pow and not curr_expr.has(sympy.Pow):
                                obs["operation_class"] = "power_dropped_error"
                            # 3. Chain rule inner derivative missing
                            elif prev_expr.has(sympy.sin) and curr_expr.has(sympy.cos):
                                obs["operation_class"] = "chain_rule_missing_inner"
                            else:
                                obs["operation_class"] = "algebraic_mutation"
                        else:
                            obs["operation_class"] = "algebraic_mutation"
                
                if obs["equivalent"]:
                    obs["operation_class"] = "valid_transformation"
            else:
                # Equation to expression or vice versa is invalid formatting
                obs["parsing_error"] = True
                
        except Exception as e:
            obs["parsing_error"] = True
            obs["error_details"] = str(e)
            
        observations.append(obs)
        
    return observations
