import collections
import copy
from app.services.simulation.process_simulator import ProbabilisticProcessSimulator
from app.services.process_evaluator import evaluate_process

def extract_process_evidence(steps):
    """
    Passes steps to ProcessEvaluator.
    Extracts the mathematical observations (not the cause).
    """
    observations = evaluate_process(steps)
    evidence = []
    for obs in observations:
        if obs["parsing_error"]:
            evidence.append("parsing_error")
        else:
            evidence.append((obs["operation_class"], obs["equivalent"]))
    return tuple(evidence)

def extract_final_answer_evidence(steps):
    """
    Extracts just the final answer string.
    """
    return steps[-1]

def build_datasets():
    archetypes = ["Strong", "Careless", "Computational", "ProceduralGap", "Multiple"]
    
    # Train questions
    train_q = [
        (3, 5, 14),
        (2, 7, 15),
        (4, 2, 10),
        (5, 1, 16),
        (6, 4, 22)
    ]
    
    # Held-out Test questions
    test_q = [
        (2, 5, 11),
        (3, 8, 17),
        (4, 3, 15),
        (5, 2, 12),
        (7, 1, 15)
    ]
    
    train_data = []
    test_data = []
    
    for arch in archetypes:
        for i in range(1500):
            sim = ProbabilisticProcessSimulator(arch, seed=hash(arch) + i)
            # Train
            t_traces = []
            for a,b,c in train_q:
                t_traces.append(sim.generate_linear_equation_work(a,b,c))
            train_data.append({"archetype": arch, "traces": t_traces})
            
            # Test
            sim2 = ProbabilisticProcessSimulator(arch, seed=hash(arch) + i + 9999)
            te_traces = []
            for a,b,c in test_q:
                te_traces.append(sim2.generate_linear_equation_work(a,b,c))
            test_data.append({"archetype": arch, "traces": te_traces})
            
    return train_data, test_data

def train_bayes(train_data):
    # P(Evidence | Archetype) for a single question trace
    fa_dist = collections.defaultdict(lambda: collections.defaultdict(float))
    proc_dist = collections.defaultdict(lambda: collections.defaultdict(float))
    arch_counts = collections.defaultdict(int)
    
    for row in train_data:
        arch = row["archetype"]
        arch_counts[arch] += len(row["traces"])
        
        for trace in row["traces"]:
            fa = extract_final_answer_evidence(trace)
            proc = extract_process_evidence(trace)
            
            fa_dist[arch][fa] += 1.0
            proc_dist[arch][proc] += 1.0
            
    for arch in arch_counts:
        total = arch_counts[arch]
        for k in fa_dist[arch]:
            fa_dist[arch][k] /= total
        for k in proc_dist[arch]:
            proc_dist[arch][k] /= total
            
    return fa_dist, proc_dist

def predict_bayes(evidence, dist, archetypes):
    best_arch = None
    max_p = -1
    for arch in archetypes:
        p = dist[arch].get(evidence, 0)
        if p > max_p:
            max_p = p
            best_arch = arch
    return best_arch

def run_ceiling_experiment():
    print("Generating Datasets...")
    train_data, test_data = build_datasets()
    
    print("Training Bayes-Optimal Classifier on Train Questions...")
    fa_dist, proc_dist = train_bayes(train_data)
    archetypes = list(fa_dist.keys())
    
    fa_correct = 0
    proc_correct = 0
    total = 0
    
    print("Evaluating on Held-Out Test Questions...")
    for row in test_data:
        arch = row["archetype"]
        for trace in row["traces"]:
            fa = extract_final_answer_evidence(trace)
            proc = extract_process_evidence(trace)
            
            p_fa = predict_bayes(fa, fa_dist, archetypes)
            p_proc = predict_bayes(proc, proc_dist, archetypes)
            
            if p_fa == arch: fa_correct += 1
            if p_proc == arch: proc_correct += 1
            total += 1
            
    print(f"Final Answer Evidence Ceiling Accuracy: {fa_correct / total * 100:.2f}%")
    print(f"Process Evidence Ceiling Accuracy: {proc_correct / total * 100:.2f}%")

if __name__ == "__main__":
    run_ceiling_experiment()
