import os
import kagglehub
import pandas as pd
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import domain

def seed_diagnostic_dataset():
    """
    Downloads the diagnostic dataset and seeds it into the database.
    """
    print("Loading Diagnostic Dataset...")
    try:
        path = "diagnostic_dataset/data"
        
        train_csv_path = os.path.join(path, "train.csv")
        mapping_csv_path = os.path.join(path, "misconception_mapping.csv")
        
        if not os.path.exists(train_csv_path):
            print(f"Could not find train.csv at {train_csv_path}")
            return
            
        df_train = pd.read_csv(train_csv_path)
        df_mapping = pd.read_csv(mapping_csv_path) if os.path.exists(mapping_csv_path) else None
        
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        return
    # Create misconception mapping dictionary
    misc_map = {}
    if df_mapping is not None:
        for _, row in df_mapping.iterrows():
            misc_map[row['MisconceptionId']] = row['MisconceptionName']
            
    # Connect to DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    print("Parsing and inserting questions into the database...")
    added_count = 0
    
    # We will just insert the first 50 questions for now to keep it fast
    # Real dataset has thousands of questions
    for index, row in df_train.iterrows():
        question_id = row['QuestionId']
        subject = row.get('SubjectName', 'Mathematics')
        topic = row.get('ConstructName', 'General')
        content = row['QuestionText']
        correct_answer = row['CorrectAnswer'] # 'A', 'B', 'C', or 'D'
        
        options = []
        for opt_letter in ['A', 'B', 'C', 'D']:
            ans_text = row.get(f'Answer{opt_letter}Text', f"Option {opt_letter}")
            is_correct = (opt_letter == correct_answer)
            
            # Find the misconception for this option if it's incorrect
            misc_id = row.get(f'Misconception{opt_letter}Id')
            diagnosis = "Mastery" if is_correct else "Unknown Error"
            
            if pd.notna(misc_id) and misc_id in misc_map:
                diagnosis = misc_map[misc_id]
                
            options.append({
                "id": opt_letter,
                "math": str(ans_text),
                "is_correct": is_correct,
                "diagnosis": diagnosis
            })
            
        # Add the "I don't know" option
        options.append({
            "id": "E",
            "math": "I don't know",
            "is_correct": False,
            "diagnosis": "Knowledge Gap (No Guessing)"
        })
        
        q = domain.Question(
            content=content,
            subject=subject,
            structural_family=topic,
            question_type="multiple_choice",
            solution=correct_answer,
            options=options
        )
        db.add(q)
        added_count += 1
        
    db.commit()
    print(f"Successfully seeded {added_count} real-world diagnostic MCQs into the database!")

if __name__ == "__main__":
    seed_diagnostic_dataset()
