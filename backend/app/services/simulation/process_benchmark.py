"""
Phase 6 Benchmark: Process-Based vs Final-Answer Diagnostic Engine.

Fixes applied:
  1. Filters questions to linear equations only (what the simulator handles)
  2. Collects ALL errors from process evaluator (not just first)
  3. Maps to 4 outcome categories: correct, arithmetic_error, wrong_op_error, mixed_error
  4. Proper ground truth: Strong → NO_SIGNIFICANT_WEAKNESS
  5. Two-tier accuracy reporting (high confidence + best guess)
"""
from app.database import SessionLocal
from app.models.domain import Question
from app.services.diagnostic_engine import DiagnosticEngine
from app.services.simulation.process_simulator import ProbabilisticProcessSimulator
from app.services.process_evaluator import evaluate_process
from app.services.final_answer_evaluator import identify_error_signature


# ── Ground truth mapping ─────────────────────────────────────────────
ARCHETYPE_TO_GROUND_TRUTH = {
    "Strong": "NO_SIGNIFICANT_WEAKNESS",
    "Careless": "CARELESS_ERROR",
    "Computational": "COMPUTATIONAL_ERROR",
    "ProceduralGap": "PROCEDURAL_GAP",
    "Multiple": "MULTIPLE_WEAKNESSES",
}


def parse_equation(q: Question):
    """Extract (a, b, c) from 'Solve: a*x + b = c'."""
    content = q.content.replace(" ", "").replace("Solve:", "")
    if "=" not in content:
        return None  # Not a linear equation
    left, right = content.split("=")
    try:
        c = int(right)
    except ValueError:
        return None

    if "+" in left:
        ax, b_str = left.split("+")
        b = int(b_str)
    elif "-" in left:
        ax, b_str = left.split("-")
        b = -int(b_str)
    else:
        ax = left
        b = 0

    a = 1
    if "*" in ax:
        a = int(ax.split("*")[0])
    return a, b, c


def categorize_process_evidence(observations: list) -> str:
    """
    Categorize ALL errors from process evaluator into a single outcome.
    This is Fix #5: collect all errors, not just the first one.
    """
    errors = [o for o in observations if not o["equivalent"] and not o.get("parsing_error")]
    if len(errors) == 0:
        return "correct"

    has_arithmetic = any(e["operation_class"] == "arithmetic" for e in errors)
    has_structural = any(
        e["operation_class"] in ("invalid_operation", "algebraic_mutation")
        for e in errors
    )

    if has_arithmetic and has_structural:
        return "mixed_error"
    elif has_arithmetic:
        return "arithmetic_error"
    elif has_structural:
        return "wrong_op_error"
    else:
        return "arithmetic_error"  # Unknown errors treated as arithmetic


def categorize_final_answer(expected_solution: str, student_final: str) -> str:
    """Categorize a final-answer comparison into an outcome key."""
    student_clean = student_final.replace("x = ", "").strip()
    if student_clean == expected_solution:
        return "correct"
    sig = identify_error_signature(expected_solution, student_clean)
    if sig in ("arithmetic_error", "incomplete_distribution"):
        return "arithmetic_error"
    if sig in ("wrong_op_error",):
        return "wrong_op_error"
    if sig in ("sign_error",):
        return "wrong_op_error"
    # Default: any numeric difference is arithmetic
    return "arithmetic_error"


def run_benchmark(num_students: int = 500):
    db = SessionLocal()
    engine = DiagnosticEngine(db)

    # Fix #1: Filter to linear equations ONLY
    all_questions = (
        db.query(Question)
        .filter(Question.structural_family.like("lin_eq_%"))
        .all()
    )
    if not all_questions:
        print("ERROR: No linear equation questions in DB. Run seed.py first.")
        return

    print(f"Using {len(all_questions)} linear equation questions for benchmark.")

    archetypes = ["Strong", "Careless", "Computational", "ProceduralGap", "Multiple"]

    results = {
        "FA": {"high": 0, "medium": 0, "insuff": 0, "wrong": 0, "total": 0},
        "Process": {"high": 0, "medium": 0, "insuff": 0, "wrong": 0, "total": 0},
    }

    for i in range(num_students):
        arch = archetypes[i % len(archetypes)]
        ground_truth = ARCHETYPE_TO_GROUND_TRUTH[arch]
        sim = ProbabilisticProcessSimulator(arch, seed=i)
        q1 = all_questions[i % len(all_questions)]

        if i % 50 == 0:
            print(f"  Processing student {i}/{num_students}...", flush=True)
        params = parse_equation(q1)
        if params is None:
            continue
        a, b, c = params

        trace1 = sim.generate_linear_equation_work(a, b, c)

        # ── Process Evidence Path ──
        obs1 = evaluate_process(trace1)
        proc_outcome = categorize_process_evidence(obs1)

        session_proc = engine.initialize_session(
            student_id=i + 10000,
            initial_skill_id=1,
            initial_evidence=proc_outcome,
            initial_question_id=q1.id,
        )
        while session_proc.status != "completed":
            nq = engine.select_next_question(session_proc)
            if not nq:
                break
            nparams = parse_equation(nq)
            if nparams is None:
                break
            na, nb, nc = nparams
            ntrace = sim.generate_linear_equation_work(na, nb, nc)
            nobs = evaluate_process(ntrace)
            n_outcome = categorize_process_evidence(nobs)
            session_proc = engine.process_answer(session_proc, nq.id, n_outcome)

        _score_result(session_proc, ground_truth, results["Process"])

        # ── Final Answer Path ──
        fa_outcome = categorize_final_answer(q1.solution, trace1[-1])

        session_fa = engine.initialize_session(
            student_id=i + 20000,
            initial_skill_id=1,
            initial_evidence=fa_outcome,
            initial_question_id=q1.id,
        )
        while session_fa.status != "completed":
            nq = engine.select_next_question(session_fa)
            if not nq:
                break
            nparams = parse_equation(nq)
            if nparams is None:
                break
            na, nb, nc = nparams
            ntrace = sim.generate_linear_equation_work(na, nb, nc)
            nfa_outcome = categorize_final_answer(nq.solution, ntrace[-1])
            session_fa = engine.process_answer(session_fa, nq.id, nfa_outcome)

        _score_result(session_fa, ground_truth, results["FA"])

        # Debug first 10
        if i < 10:
            p_diag = session_proc.diagnosis or {}
            f_diag = session_fa.diagnosis or {}
            print(
                f"  Student {i:3d} ({arch:15s} -> {ground_truth:25s}) | "
                f"Process: {p_diag.get('primary_cause', '?'):25s} ({p_diag.get('confidence_tier', '?'):6s}) | "
                f"FA: {f_diag.get('primary_cause', '?'):25s} ({f_diag.get('confidence_tier', '?'):6s})"
            )

    # ── Print results ──
    print(f"\n{'='*70}")
    print(f"Phase 6 Benchmark — {num_students} students")
    print(f"{'='*70}")
    for label, r in results.items():
        total = r["total"]
        if total == 0:
            continue
        high_acc = r["high"] / total * 100
        med_acc = r["medium"] / total * 100
        combined = (r["high"] + r["medium"]) / total * 100
        insuff = r["insuff"] / total * 100
        wrong = r["wrong"] / total * 100
        print(f"\n{label} Engine:")
        print(f"  High-confidence correct: {r['high']:4d} / {total} = {high_acc:5.1f}%")
        print(f"  Best-guess correct:      {r['medium']:4d} / {total} = {med_acc:5.1f}%")
        print(f"  Combined accuracy:       {r['high']+r['medium']:4d} / {total} = {combined:5.1f}%")
        print(f"  Insufficient evidence:   {r['insuff']:4d} / {total} = {insuff:5.1f}%")
        print(f"  Wrong diagnosis:         {r['wrong']:4d} / {total} = {wrong:5.1f}%")

    db.close()


def _score_result(session, ground_truth: str, result_dict: dict):
    """Score a completed session against ground truth."""
    result_dict["total"] += 1
    diag = (session.diagnosis or {}).get("primary_cause", "INSUFFICIENT_EVIDENCE")
    tier = (session.diagnosis or {}).get("confidence_tier", "low")

    if diag == ground_truth:
        if tier == "high":
            result_dict["high"] += 1
        else:
            result_dict["medium"] += 1
    elif diag == "INSUFFICIENT_EVIDENCE":
        result_dict["insuff"] += 1
    else:
        result_dict["wrong"] += 1


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    run_benchmark(500)
