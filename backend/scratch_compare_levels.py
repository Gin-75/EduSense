import json
import math

def calculate_kl(p, q, epsilon=1e-6):
    kl = 0.0
    keys = set(p.keys()) | set(q.keys())
    for k in keys:
        p_smooth = (p.get(k, 0) + epsilon) / (1.0 + len(keys) * epsilon)
        q_smooth = (q.get(k, 0) + epsilon) / (1.0 + len(keys) * epsilon)
        kl += p_smooth * math.log2(p_smooth / q_smooth)
    return kl

def compare_levels():
    with open("identifiability_matrix.json", "r") as f:
        l1 = json.load(f)
    try:
        with open("identifiability_matrix_level2.json", "r") as f:
            l2 = json.load(f)
    except:
        print("Wait for l2 to finish")
        return
        
    pairs = [
        ("Careless Error Student", "Arithmetic Weakness"),
        ("Arithmetic Weakness", "Multiple Weaknesses"),
        ("Multiple Weaknesses", "Insufficient Evidence"),
        ("Careless Error Student", "Strong Student"),
        ("Arithmetic Weakness", "Strong Student")
    ]
    
    print(f"{'Pair':<50} | {'L1 KL':<10} | {'L2 KL':<10}")
    print("-" * 75)
    
    for a1, a2 in pairs:
        # L1
        l1_kl = max([calculate_kl(l1[a1][q], l1[a2][q]) for q in l1[a1]])
        
        # L2
        l2_kl = max([calculate_kl(l2[a1][q], l2[a2][q]) for q in l2[a1]])
        
        print(f"{a1} vs {a2:<20} | {l1_kl:<10.3f} | {l2_kl:<10.3f}")

if __name__ == "__main__":
    compare_levels()
