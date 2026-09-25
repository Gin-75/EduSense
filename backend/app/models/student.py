from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)


class Attempt(Base):
    """
    Represents a student's attempt at answering a question.
    Stores the parsed work, correctness, and the mapped error signature.
    """
    __tablename__ = "attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer = Column(Text)
    parsed_work = Column(JSON, nullable=True) # Step-by-step parsed representation
    correctness = Column(Float, default=0.0) # 0.0 to 1.0
    error_signature = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student")
    # question = relationship("Question") # Can be imported if needed


class StudentSkillState(Base):
    """
    Dynamic probabilistic model of a student's knowledge.
    """
    __tablename__ = "student_skill_state"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    mastery = Column(Float, default=0.5) # Probability of mastery
    confidence = Column(Float, default=0.1) # Confidence in the mastery estimate
    evidence_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class DiagnosticSession(Base):
    """
    Tracks an active diagnostic drill-down session.
    """
    __tablename__ = "diagnostic_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    initial_skill_id = Column(Integer, ForeignKey("skills.id"))
    hypotheses = Column(JSON) # e.g., {"skill_id_1": 0.3, "misconception_id_2": 0.6}
    attempts_history = Column(JSON) # List of attempt IDs inside this session
    diagnosis = Column(JSON, nullable=True) # Final resolved diagnosis
    confidence = Column(Float, default=0.0)
    status = Column(String, default="active") # "active", "completed"
    
    # Traceability & state arrays
    asked_questions = Column(JSON, default=list) 
    hypothesis_history = Column(JSON, default=list)
    selection_rationale = Column(JSON, default=list)
    evidence_history = Column(JSON, default=list)
    confidence_history = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
