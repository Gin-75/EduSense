"""
Hierarchical ground truth definition.

This module defines the structured latent state that the Diagnostic Engine
is attempting to discover. It is kept strictly isolated from the engine.
"""

from typing import List, Optional
from pydantic import BaseModel

class GroundTruth(BaseModel):
    """
    The hidden root cause of a synthetic student's errors.
    This is hierarchical to allow multi-level evaluation.
    """
    category: str  # e.g. "MISCONCEPTION", "COMPUTATIONAL_ERROR", "PROCEDURAL_GAP"
    specific_cause: Optional[str] = None  # e.g. "incomplete_distribution"
    affected_skills: List[str] = []  # e.g. ["distributive_property"]
    secondary_causes: List[str] = []
