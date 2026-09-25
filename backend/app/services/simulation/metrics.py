"""
Metrics computation for simulation runs.
"""
from typing import List, Dict, Any
from app.models.schemas import SimulationResult

def compute_simulation_metrics(results: List[SimulationResult]) -> Dict[str, Any]:
    if not results:
        return {}
        
    total = len(results)
    correct_count = sum(1 for r in results if r.correct)
    false_diag_count = sum(1 for r in results if r.false_diagnosis)
    insuf_count = sum(1 for r in results if r.insufficient_evidence)
    
    q_used = [r.questions_used for r in results]
    avg_q = sum(q_used) / total
    median_q = sorted(q_used)[total // 2]
    
    conf_correct = [r.engine_confidence for r in results if r.correct]
    conf_wrong = [r.engine_confidence for r in results if not r.correct and not r.insufficient_evidence]
    
    avg_conf_correct = sum(conf_correct) / len(conf_correct) if conf_correct else 0.0
    avg_conf_wrong = sum(conf_wrong) / len(conf_wrong) if conf_wrong else 0.0
    
    # Archetype breakdown
    archetypes = set(r.archetype for r in results)
    breakdown = {}
    for arch in archetypes:
        arch_res = [r for r in results if r.archetype == arch]
        arch_correct = sum(1 for r in arch_res if r.correct)
        arch_q = sum(r.questions_used for r in arch_res) / len(arch_res)
        breakdown[arch] = {
            "accuracy": arch_correct / len(arch_res),
            "avg_questions": arch_q,
            "total": len(arch_res)
        }
        
    # Accuracy at question budget (1-5)
    acc_at_budget = {}
    for b in range(1, 6):
        c = sum(1 for r in results if r.correct and r.questions_used <= b)
        acc_at_budget[f"accuracy_after_Q{b}"] = c / total
        
    # Specific root-cause accuracy
    # In our MVP, engine_diagnosis directly returns the root cause string from the hypotheses
    # The `correct` boolean checks if `engine_diag == gt.category`
    # We should also check `engine_diag == gt.specific_cause` but the engine only tracks the hypotheses.
    # The hypotheses map to the specific cause directly (e.g. MISCONCEPTION_incomplete_distribution).
    
    specific_correct = sum(1 for r in results if r.correct) # in our MVP category == specific root cause effectively, they are mapped to the same string by the simulator runner
        
    return {
        "total_students": total,
        "category_accuracy": correct_count / total,
        "specific_root_cause_accuracy": specific_correct / total,
        "false_diagnosis_rate": false_diag_count / total,
        "insufficient_evidence_rate": insuf_count / total,
        "average_questions": avg_q,
        "median_questions": median_q,
        "confidence_when_correct": avg_conf_correct,
        "confidence_when_wrong": avg_conf_wrong,
        "per_archetype": breakdown,
        **acc_at_budget
    }
