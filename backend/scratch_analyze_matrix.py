import json
from collections import defaultdict
import math

def calculate_kl(p, q, epsilon=1e-6):
    """Calculate KL divergence D(P || Q) for discrete distributions"""
    kl = 0.0
    for k in set(p.keys()) | set(q.keys()):
        p_val = p.get(k, 0)
        q_val = q.get(k, 0)
        # Smooth
        p_smooth = (p_val + epsilon) / (1.0 + len(set(p.keys()) | set(q.keys())) * epsilon)
        q_smooth = (q_val + epsilon) / (1.0 + len(set(p.keys()) | set(q.keys())) * epsilon)
        kl += p_smooth * math.log2(p_smooth / q_smooth)
    return kl

def analyze_identifiability():
    try:
        with open("identifiability_matrix.json", "r") as f:
            matrix = json.load(f)
    except FileNotFoundError:
        print("identifiability_matrix.json not found yet")
        return
        
    archetypes = list(matrix.keys())
    
    # 1. Separability matrix
    print("--- PAIRWISE DISTINGUISHABILITY (MAX KL DIVERGENCE FROM SINGLE QUESTION) ---")
    for i in range(len(archetypes)):
        for j in range(i+1, len(archetypes)):
            a1 = archetypes[i]
            a2 = archetypes[j]
            
            max_kl = 0
            best_q = None
            
            for q_id in matrix[a1]:
                p = matrix[a1][q_id]
                q = matrix[a2][q_id]
                kl = calculate_kl(p, q)
                if kl > max_kl:
                    max_kl = kl
                    best_q = q_id
                    
            status = "SEPARABLE" if max_kl > 0.5 else ("WEAKLY SEPARABLE" if max_kl > 0.1 else "INDISTINGUISHABLE")
            print(f"{a1} vs {a2} -> {status} (Max KL: {max_kl:.3f} on Q{best_q})")
            
    # 2. Can 5 questions achieve 80% confidence?
    # To go from uniform 1/6 (0.166) to 0.8, the likelihood ratio needs to be 0.8/0.2 / (1/5) = 4 / 0.2 = 20.
    # log2(20) ~ 4.32 bits of evidence.
    print("\n--- MINIMUM QUESTIONS TO 80% CONFIDENCE ---")
    for a1 in archetypes:
        # Find the minimum KL divergence to any OTHER archetype.
        # This is the bottleneck for identifying a1.
        min_kl_to_others = float('inf')
        closest_arch = None
        
        for a2 in archetypes:
            if a1 == a2: continue
            
            # Sum of max KL across questions? 
            # Or just take the max KL we can get from the best question?
            # Let's say we repeatedly ask the best question (assuming independence for theoretical limit)
            max_kl_single = max(calculate_kl(matrix[a1][q], matrix[a2][q]) for q in matrix[a1])
            if max_kl_single < min_kl_to_others:
                min_kl_to_others = max_kl_single
                closest_arch = a2
                
        if min_kl_to_others > 0:
            min_questions = math.ceil(4.32 / min_kl_to_others)
            print(f"{a1}: Requires >= {min_questions} questions (Closest distractor: {closest_arch} with KL {min_kl_to_others:.3f})")
        else:
            print(f"{a1}: IDENTIFICATION IMPOSSIBLE (Identical to {closest_arch})")

if __name__ == "__main__":
    analyze_identifiability()
