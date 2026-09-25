import numpy as np
import torch
from EduCDM import NCDM
import os

# 1. Define the Q-matrix (Items vs Skills)
# We will align this with the Egyptian Mathematics Curriculum (Sec 2 & Sec 3)
# Skills (Knowledge Concepts):
# 0: Pure Math: Limits & Continuity (Sec 2)
# 1: Pure Math: Differentiation Foundations (Sec 2)
# 2: Pure Math: Integration & Applications (Sec 3)
# 3: Applied Math: Statics/Moments (Sec 3)
# 4: Applied Math: Dynamics/Newton (Sec 3)

NUM_ITEMS = 20
NUM_SKILLS = 5
NUM_STUDENTS = 1000

q_m = np.zeros((NUM_ITEMS, NUM_SKILLS))

# Items 0-3: Limits & Continuity
q_m[0:4, 0] = 1 
# Items 4-7: Differentiation
q_m[4:8, 1] = 1
# Items 8-11: Integration (Needs Differentiation too)
q_m[8:12, 1] = 1
q_m[8:12, 2] = 1
# Items 12-15: Statics
q_m[12:16, 3] = 1
# Items 16-19: Dynamics (Often requires basic calculus)
q_m[16:20, 1] = 1
q_m[16:20, 4] = 1

from torch.utils.data import Dataset, DataLoader

class NCDMDataset(Dataset):
    def __init__(self, data_list, q_m):
        self.data = data_list
        self.q_m = torch.FloatTensor(q_m)
        
    def __len__(self):
        return len(self.data)
        
    def __getitem__(self, idx):
        item = self.data[idx]
        user_id = torch.tensor(item['user_id'], dtype=torch.int64)
        item_id = torch.tensor(item['item_id'], dtype=torch.int64)
        # NCDM expects the knowledge_emb to be the row of the Q-matrix
        knowledge_emb = self.q_m[item['item_id']]
        y = torch.tensor(item['score'], dtype=torch.float32)
        return user_id, item_id, knowledge_emb, y

# Generate lists
train_list = []
student_profiles = np.random.rand(NUM_STUDENTS, NUM_SKILLS)
for u in range(NUM_STUDENTS):
    profile = student_profiles[u]
    for i in range(NUM_ITEMS):
        required_skills = q_m[i]
        if np.sum(required_skills) > 0:
            mastery = np.sum(profile * required_skills) / np.sum(required_skills)
        else:
            mastery = 0.5
        prob = mastery * 0.8 + 0.1
        score = 1 if np.random.rand() < prob else 0
        train_list.append({'user_id': u, 'item_id': i, 'score': score})

test_list = train_list[-4000:]
train_list = train_list[:-4000]

train_dataset = NCDMDataset(train_list, q_m)
test_dataset = NCDMDataset(test_list, q_m)

# EduCDM expects an iterable yielding batches
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

print("Initializing NCDM model...")
cdm = NCDM(NUM_SKILLS, NUM_ITEMS, NUM_STUDENTS)

print("Training NCDM model (this may take a moment)...")
cdm.train(train_loader, test_loader, epoch=2, device="cpu")

model_dir = "app/models/cdm"
os.makedirs(model_dir, exist_ok=True)
cdm.save(os.path.join(model_dir, "ncdm.params"))
np.save(os.path.join(model_dir, "q_matrix.npy"), q_m)

print("NCDM Model trained and saved to app/models/cdm/ncdm.params")
