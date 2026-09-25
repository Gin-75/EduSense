import math
import collections
from simulator import generate_equation_dataset

def train_bayes(dataset):
    fa_dist = collections.defaultdict(lambda: collections.defaultdict(float))
    proc_dist = collections.defaultdict(lambda: collections.defaultdict(float))
    arch_counts = collections.defaultdict(int)
    
    for row in dataset:
        arch = row["archetype"]
        traces = row["traces"]
        arch_counts[arch] += 1
        
        fa_evidence = tuple(t[-1]["after"] for t in traces)
        fa_dist[arch][fa_evidence] += 1
        
        proc_evidence_list = []
        for t in traces:
            q_ev = []
            for step in t:
                q_ev.append((step["before"], step["operation"], step["after"], step["valid"]))
            proc_evidence_list.append(tuple(q_ev))
        proc_evidence = tuple(proc_evidence_list)
        
        proc_dist[arch][proc_evidence] += 1
        
    for arch in fa_dist:
        total = arch_counts[arch]
        for k in fa_dist[arch]:
            fa_dist[arch][k] /= total
            
    for arch in proc_dist:
        total = arch_counts[arch]
        for k in proc_dist[arch]:
            proc_dist[arch][k] /= total
            
    return fa_dist, proc_dist, arch_counts

def predict_bayes_optimal(evidence, dist, arch_counts):
    best_arch = None
    max_prob = -1
    
    for arch in arch_counts:
        prob = dist[arch].get(evidence, 0)
        if prob > max_prob:
            max_prob = prob
            best_arch = arch
    return best_arch

def evaluate_classifier():
    print("Generating equation dataset...")
    train_ds = generate_equation_dataset(10000)
    fa_dist, proc_dist, arch_counts = train_bayes(train_ds)
    
    test_ds = generate_equation_dataset(2000)
    
    fa_correct = 0
    proc_correct = 0
    total = len(test_ds)
    
    fa_confusion = collections.defaultdict(int)
    proc_confusion = collections.defaultdict(int)
    
    for row in test_ds:
        arch = row["archetype"]
        traces = row["traces"]
        
        fa_evidence = tuple(t[-1]["after"] for t in traces)
        proc_evidence_list = []
        for t in traces:
            q_ev = []
            for step in t:
                q_ev.append((step["before"], step["operation"], step["after"], step["valid"]))
            proc_evidence_list.append(tuple(q_ev))
        proc_evidence = tuple(proc_evidence_list)
        
        fa_pred = predict_bayes_optimal(fa_evidence, fa_dist, arch_counts)
        proc_pred = predict_bayes_optimal(proc_evidence, proc_dist, arch_counts)
        
        if fa_pred == arch:
            fa_correct += 1
        if fa_pred is not None:
            fa_confusion[(arch, fa_pred)] += 1
            
        if proc_pred == arch:
            proc_correct += 1
        if proc_pred is not None:
            proc_confusion[(arch, proc_pred)] += 1
            
    print(f"\nFinal Answer Accuracy: {fa_correct / total * 100:.2f}%")
    print(f"Process Accuracy: {proc_correct / total * 100:.2f}%")
    
    print("\nProcess Confusion Matrix (True -> Pred):")
    for (t, p), v in sorted(proc_confusion.items()):
        if t != p and v > 50:
            print(f"  {t} -> {p}: {v}")
            
    print("\nFinal Answer Confusion Matrix (True -> Pred):")
    for (t, p), v in sorted(fa_confusion.items()):
        if t != p and v > 50:
            print(f"  {t} -> {p}: {v}")

    # Same-final-answer test
    print("\n--- SAME FINAL ANSWER TEST ---")
    # Let's find an example where FA is the same but process is different
    # x + 5 = 12 -> x = 17
    # Trace 1: Procedural Gap (x = 12 + 5 -> x = 17)
    # Trace 2: Computational Weakness (x = 12 - 5 -> x = 17)
    print("Example: x + 5 = 12")
    
    fa_ex = "x = 17"
    proc_ex1 = (("x + 5 = 12", "inverse_operation", "x = 12 + 5", False), ("x = 12 + 5", "arithmetic", "x = 17", True))
    proc_ex2 = (("x + 5 = 12", "inverse_operation", "x = 12 - 5", True), ("x = 12 - 5", "arithmetic", "x = 17", False))
    
    # We will compute the posterior probability (using Bayes rule) for a single question response for simplicity
    print("Student A trace:", proc_ex1)
    print("Student B trace:", proc_ex2)

if __name__ == "__main__":
    evaluate_classifier()
