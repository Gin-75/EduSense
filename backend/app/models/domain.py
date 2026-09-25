from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)
    subject = Column(String, index=True)
    difficulty = Column(Float, default=0.5)

    # Relationships
    misconceptions = relationship("Misconception", back_populates="related_skill")
    # For dependencies, we'll define a separate table and use it to build the graph dynamically


class SkillDependency(Base):
    """
    Typed Knowledge Graph relationships.
    relationship_type can be: REQUIRES, SUPPORTS, APPLIES_TO, PREREQUISITE_OF, RELATED_TO, CONFUSED_WITH
    """
    __tablename__ = "skill_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    source_skill_id = Column(Integer, ForeignKey("skills.id"))
    target_skill_id = Column(Integer, ForeignKey("skills.id"))
    relationship_type = Column(String)  # e.g., "REQUIRES", "OFTEN_CONFUSED_WITH"
    strength = Column(Float, default=1.0)


class Misconception(Base):
    __tablename__ = "misconceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    related_skill_id = Column(Integer, ForeignKey("skills.id"))
    
    related_skill = relationship("Skill", back_populates="misconceptions")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    subject = Column(String, index=True)
    difficulty = Column(Float, default=0.5)
    question_type = Column(String)  # e.g., "equation", "multiple_choice", "step_by_step"
    solution = Column(Text)  # Expected answer or SymPy interpretable expression
    options = Column(JSON, nullable=True) # Diagnostic MCQ options
    structural_family = Column(String, nullable=True) # e.g. "binomial_distribution"
    diagnostic_properties = Column(JSON, nullable=True) # Expected error signatures and outcomes
    
    # Relationships
    skills = relationship("QuestionSkill", back_populates="question")
    misconceptions = relationship("QuestionMisconception", back_populates="question")


class QuestionSkill(Base):
    __tablename__ = "question_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    relevance = Column(Float, default=1.0)
    
    question = relationship("Question", back_populates="skills")
    skill = relationship("Skill")


class QuestionMisconception(Base):
    """
    Maps a question to a specific misconception it's designed to diagnose.
    """
    __tablename__ = "question_misconceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    misconception_id = Column(Integer, ForeignKey("misconceptions.id"))
    diagnostic_value = Column(Float, default=1.0) # Information Gain estimation
    
    question = relationship("Question", back_populates="misconceptions")
    misconception = relationship("Misconception")
