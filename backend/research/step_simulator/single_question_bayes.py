import collections
from simulator import generate_equation_dataset

def get_posteriors():
    train_ds = generate_equation_dataset(20000)
    
    fa_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    proc_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    arch_counts = collections.defaultdict(int)
    
    for row in train_ds:
        arch = row["archetype"]
        arch_counts[arch] += 1
        
        # Look at the first question only for posterior
        t = row["traces"][0]
        
        fa = t[-1]["after"]
        fa_counts[fa][arch] += 1
        
        proc_ev = []
        for step in t:
            proc_ev.append((step["before"], step["operation"], step["after"], step["valid"]))
        proc_ev = tuple(proc_ev)
        proc_counts[proc_ev][arch] += 1
        
    print("--- Single Question Posteriors ---")
    fa_ex = "x = 17"
    print(f"\nGiven Final Answer: {fa_ex}")
    total_fa = sum(fa_counts[fa_ex].values())
    if total_fa > 0:
        for arch, count in fa_counts[fa_ex].items():
            print(f"  {arch}: {count/total_fa*100:.1f}%")
            
    proc_ex1 = (('x + 5 = 12', 'inverse_operation', 'x = 12 + 5', False), ('x = 12 + 5', 'arithmetic', 'x = 17', True))
    print("\nGiven Process A (Wrong Op, Correct Math):")
    total_proc1 = sum(proc_counts[proc_ex1].values())
    if total_proc1 > 0:
        for arch, count in proc_counts[proc_ex1].items():
            print(f"  {arch}: {count/total_proc1*100:.1f}%")
            
    proc_ex2 = (('x + 5 = 12', 'inverse_operation', 'x = 12 - 5', True), ('x = 12 - 5', 'arithmetic', 'x = 17', False))
    print("\nGiven Process B (Correct Op, Wrong Math):")
    total_proc2 = sum(proc_counts[proc_ex2].values())
    if total_proc2 > 0:
        for arch, count in proc_counts[proc_ex2].items():
            print(f"  {arch}: {count/total_proc2*100:.1f}%")

if __name__ == "__main__":
    get_posteriors()
