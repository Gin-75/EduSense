"""
Root Cause Taxonomy for the Diagnostic Evaluator.

This module defines the controlled vocabulary used to classify the
underlying cause of a student's error.  The taxonomy is deliberately
kept separate from error *signatures* (which describe WHAT happened)
so that the evaluator reasons about WHY it happened.

The enum is extensible: new members can be added without breaking
existing evaluation records because the DB stores the string value.
"""

from enum import Enum


class RootCauseCategory(str, Enum):
    """Broad category of the underlying cause of a student error."""

    CONCEPTUAL_GAP = "CONCEPTUAL_GAP"
    PROCEDURAL_GAP = "PROCEDURAL_GAP"
    COMPUTATIONAL_ERROR = "COMPUTATIONAL_ERROR"
    REPRESENTATION_ERROR = "REPRESENTATION_ERROR"
    INTERPRETATION_ERROR = "INTERPRETATION_ERROR"
    MISCONCEPTION = "MISCONCEPTION"
    CARELESS_ERROR = "CARELESS_ERROR"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DiagnosticQuality(str, Enum):
    """How well the engine's diagnosis is supported by evidence."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
