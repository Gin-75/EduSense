import numpy as np
import torch
from EduCDM import DINA
import json
import os

# 1. Define the Q-matrix (Items vs Skills)
# Skills: 
# 0: Basic Algebra
# 1: Differentiation (Power Rule)
# 2: Differentiation (Chain Rule)
# 3: Integration (Power Rule)
# 4: Integration by Parts
# 5: Missing +C Awareness

NUM_ITEMS = 20
NUM_SKILLS = 6
NUM_STUDENTS = 1000

# Let's mock a Q-matrix for 20 items.
q_m = np.zeros((NUM_ITEMS, NUM_SKILLS))

# Items 0-4: Basic Algebra
q_m[0:5, 0] = 1 

# Items 5-8: Power Rule
q_m[5:9, 1] = 1

# Items 9-12: Chain Rule (also requires Power Rule)
q_m[9:13, 1] = 1
q_m[9:13, 2] = 1

# Items 13-16: Integration Power Rule & +C
q_m[13:17, 3] = 1
q_m[13:17, 5] = 1

# Items 17-19: Integration by Parts (requires Chain Rule, Power Rule, Int Power Rule)
q_m[17:20, 2] = 1
q_m[17:20, 3] = 1
q_m[17:20, 4] = 1
q_m[17:20, 5] = 1

# 2. Generate Synthetic Student Data
# We will simulate 1000 students. Each student has a true mastery profile (0 or 1 for each skill).
# If they have all required skills for an item, they get it right 90% of the time (10% slip).
# If they lack a required skill, they get it right 20% of the time (20% guess).

train_data = []
student_profiles = np.random.randint(2, size=(NUM_STUDENTS, NUM_SKILLS))

for u in range(NUM_STUDENTS):
    profile = student_profiles[u]
    for i in range(NUM_ITEMS):
        required_skills = q_m[i]
        # Check if student has all required skills
        has_skills = np.all(profile >= required_skills)
        
        if has_skills:
            score = 1 if np.random.rand() > 0.1 else 0
        else:
            score = 1 if np.random.rand() < 0.2 else 0
            
        train_data.append({
            'user_id': u,
            'item_id': i,
            'score': score
        })

print(f"Generated {len(train_data)} interactions for {NUM_STUDENTS} students.")

# 3. Train DINA Model
print("Initializing DINA model...")
cdm = DINA(NUM_STUDENTS, NUM_ITEMS, NUM_SKILLS)

print("Training DINA model (this may take a moment)...")
# DINA uses EM algorithm
cdm.train(train_data, q_m, epoch=2, epsilon=1e-3)

# 4. Save the model
model_dir = "app/models/cdm"
os.makedirs(model_dir, exist_ok=True)
cdm.save(os.path.join(model_dir, "dina.params"))

# Also save the Q-matrix so the API can use it
np.save(os.path.join(model_dir, "q_matrix.npy"), q_m)

print("Model trained and saved to app/models/cdm/dina.params")

# 5. Quick Test: Predict for a student
test_student_log = [
    {'user_id': 0, 'item_id': 0, 'score': 1}, # Algebra (Correct)
    {'user_id': 0, 'item_id': 6, 'score': 0}, # Power Rule (Wrong)
]
# Wait, DINA's diagnosis usually diagnoses all students it was trained on. 
# To diagnose a *new* student on the fly in production, we can use the learned item parameters
# (guess and slip) to compute the posterior probability of the student's mastery profile.
# We will implement that logic in the diagnostic engine.
