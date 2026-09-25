import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

has_genai = False
try:
    import google.generativeai as genai
    has_genai = True
    
    # Configure Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    else:
        print("WARNING: GEMINI_API_KEY not found. LLM Analysis will fall back to rule-based.")
except ImportError:
    print("WARNING: google.generativeai is not installed.")
    api_key = None

def analyze_student_error_llm(question_content: str, expected_solution: str, student_trace: list, subject: str = "Math", construct: str = "General") -> Dict[str, str]:
    """
    Uses Gemini to analyze the student's step-by-step trace and determine the exact cognitive bottleneck.
    Adopts the prompt architecture from advanced cognitive diagnosis models.
    """
    if not api_key:
        return {
            "primary_cause": "Configuration Required",
            "report": "Please add GEMINI_API_KEY to your backend .env file to enable AI-powered cognitive analysis."
        }
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        student_final_answer = student_trace[-1] if student_trace else ""
        trace_text = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(student_trace)])
        
        # Architecture for accurate zero-shot cognitive diagnosis
        prompt = f"""
Here is a question about {construct} ({subject}).
Question: {question_content}
Correct Answer: {expected_solution}
Student's Incorrect Answer / Trace: 
{trace_text}

You are an expert Mathematics teacher. Your task is to reason and identify the specific cognitive misconception behind the student's incorrect answer.
First, identify the exact mathematical misconception (e.g., "Confuses perimeter with area", "Subtracts instead of dividing", "Fails to distribute negative sign"). 
Then, write a 2-sentence empathetic, pedagogical explanation for the student explaining where they went wrong.

Respond EXACTLY in this format:
BOTTLENECK: [A concise, 3-10 word official-sounding misconception name]
REPORT: [Your 2-sentence pedagogical feedback]
"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        bottleneck = "Unknown Error"
        report = "Could not analyze the error."
        
        for line in text.split('\n'):
            if line.startswith("BOTTLENECK:"):
                bottleneck = line.replace("BOTTLENECK:", "").strip()
            elif line.startswith("REPORT:"):
                report = line.replace("REPORT:", "").strip()
                
        return {
            "primary_cause": bottleneck,
            "report": report
        }
        
    except Exception as e:
        return {
            "primary_cause": "Analysis Failed",
            "report": f"LLM Error: {str(e)}"
        }

def generate_session_summary_llm(mastery_profile: dict) -> str:
    """Generates an encouraging summary based on their BKT mastery."""
    if not api_key:
        return "You have completed the assessment. Review your mastery profile."
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        skills_str = ", ".join([f"{k}: {int(v*100)}%" for k, v in mastery_profile.items()])
        prompt = f"""
You are an encouraging math tutor. The student just finished a diagnostic assessment.
Here is their final mastery profile across various micro-skills:
{skills_str}

Write a 2-sentence encouraging summary of their performance. Highlight their strongest skill and point out one area they should focus on next.
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Assessment complete. Great job working through the problems!"
