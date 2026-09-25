import collections
from app.services.simulation.process_simulator import ProbabilisticProcessSimulator
from app.services.simulation.evidence_ceiling import extract_process_evidence, extract_final_answer_evidence

def build_datasets(noise_multiplier=1.0):
    archetypes = ["Strong", "Careless", "Computational", "ProceduralGap", "Multiple"]
    train_q = [(3, 5, 14), (2, 7, 15), (4, 2, 10)]
    test_q = [(2, 5, 11), (3, 8, 17), (4, 3, 15)]
    
    train_data = []
    test_data = []
    
    for arch in archetypes:
        for i in range(200):
            # Train
            sim = ProbabilisticProcessSimulator(arch, seed=hash(arch) + i)
            sim.p_careless = min(1.0, sim.p_careless * noise_multiplier)
            t_traces = [sim.generate_linear_equation_work(*q) for q in train_q]
            train_data.append({"archetype": arch, "traces": t_traces})
            
            # Test
            sim2 = ProbabilisticProcessSimulator(arch, seed=hash(arch) + i + 9999)
            sim2.p_careless = min(1.0, sim2.p_careless * noise_multiplier)
            te_traces = [sim2.generate_linear_equation_work(*q) for q in test_q]
            test_data.append({"archetype": arch, "traces": te_traces})
            
    return train_data, test_data

def evaluate(train_data, test_data):
    fa_dist = collections.defaultdict(lambda: collections.defaultdict(float))
    proc_dist = collections.defaultdict(lambda: collections.defaultdict(float))
    arch_counts = collections.defaultdict(int)
    
    for row in train_data:
        arch = row["archetype"]
        arch_counts[arch] += len(row["traces"])
        for trace in row["traces"]:
            fa_dist[arch][extract_final_answer_evidence(trace)] += 1.0
            proc_dist[arch][extract_process_evidence(trace)] += 1.0
            
    for arch in arch_counts:
        total = arch_counts[arch]
        for k in fa_dist[arch]: fa_dist[arch][k] /= total
        for k in proc_dist[arch]: proc_dist[arch][k] /= total
            
    fa_correct = 0
    proc_correct = 0
    total = 0
    
    archetypes = list(fa_dist.keys())
    
    for row in test_data:
        arch = row["archetype"]
        for trace in row["traces"]:
            fa = extract_final_answer_evidence(trace)
            proc = extract_process_evidence(trace)
            
            # Predict
            best_fa = max(archetypes, key=lambda a: fa_dist[a].get(fa, 0))
            best_proc = max(archetypes, key=lambda a: proc_dist[a].get(proc, 0))
            
            if best_fa == arch: fa_correct += 1
            if best_proc == arch: proc_correct += 1
            total += 1
            
    return fa_correct/total, proc_correct/total

def run_falsification():
    for noise in [1.0, 2.0, 4.0]:
        print(f"--- Noise Multiplier: {noise}x ---")
        tr, te = build_datasets(noise)
        fa_acc, proc_acc = evaluate(tr, te)
        print(f"Final Answer: {fa_acc*100:.1f}% | Process: {proc_acc*100:.1f}%")

if __name__ == "__main__":
    run_falsification()
