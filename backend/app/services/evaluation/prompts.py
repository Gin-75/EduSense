"""
LLM Prompt Templates — two-call architecture for independent evaluation.

CALL 1:  Independent diagnosis (no engine prediction visible).
CALL 2:  Comparison (engine prediction revealed).

These templates are provider-agnostic.  They produce plain strings that
any LLM provider can send to its respective API.
"""

from __future__ import annotations

import json

from app.models.schemas import (
    EnginePrediction,
    EvaluationCaseInput,
    IndependentDiagnosis,
)


# ── Call 1 — Independent Diagnosis ────────────────────────────────────

INDEPENDENT_DIAGNOSIS_SYSTEM = """\
You are an independent diagnostic evaluator for an Adaptive Diagnostic Assessment Engine.

Your job is NOT to solve the student's problem.
Your primary objective is to determine the student's most likely underlying ROOT CAUSE of failure from their responses, attempts, errors, and diagnostic history.

IMPORTANT RULES:
1. Do NOT assume that every wrong answer means lack of knowledge.
2. Distinguish between:
   - CONCEPTUAL_GAP
   - PROCEDURAL_GAP
   - COMPUTATIONAL_ERROR
   - REPRESENTATION_ERROR
   - INTERPRETATION_ERROR
   - MISCONCEPTION
   - CARELESS_ERROR
   - INSUFFICIENT_EVIDENCE
3. Consider multiple competing hypotheses before selecting a root cause.
4. Repeated structurally similar errors are stronger evidence than a single mistake.
5. A correct answer does NOT automatically prove mastery.
6. A wrong answer does NOT automatically prove lack of mastery.
7. Do not invent evidence that is not present in the student's data.
8. If the evidence is insufficient to identify a root cause, return INSUFFICIENT_EVIDENCE.
9. Separate the observed error from the underlying cause.

DIAGNOSTIC PROCESS:
Step 1 — Analyze the student's responses. Identify exactly what the student did wrong.
Step 2 — Identify the mathematical skill involved.
Step 3 — Generate competing hypotheses for the underlying cause.
Step 4 — For each hypothesis, identify supporting and contradicting evidence.
Step 5 — Determine which hypothesis is best supported.
Step 6 — Estimate your confidence (0.0 to 1.0).
Step 7 — Identify what additional question would most effectively distinguish between the remaining hypotheses.

Return your analysis as a JSON object with exactly this structure:
{
  "observed_error": "...",
  "skill_involved": "...",
  "hypotheses": [
    {
      "cause": "MISCONCEPTION | CONCEPTUAL_GAP | ...",
      "confidence": 0.0,
      "supporting_evidence": ["..."],
      "contradicting_evidence": ["..."]
    }
  ],
  "independent_root_cause": "MISCONCEPTION | CONCEPTUAL_GAP | ...",
  "specific_label": "e.g. incomplete_distribution (or null)",
  "confidence": 0.0,
  "evidence_summary": ["..."],
  "most_informative_next_question": "..."
}

Return ONLY valid JSON. No markdown fences, no explanation outside the JSON."""


def build_independent_diagnosis_prompt(case: EvaluationCaseInput) -> str:
    """Build the user-message for Call 1."""
    responses_text = []
    for i, r in enumerate(case.student_responses, 1):
        entry = (
            f"Attempt {i}:\n"
            f"  Question: {r.question_content}\n"
            f"  Expected: {r.expected_answer}\n"
            f"  Student answered: {r.student_answer}\n"
            f"  Correct: {r.is_correct}\n"
            f"  Error signature: {r.error_signature or 'N/A'}\n"
            f"  Skills: {', '.join(r.skill_names) or 'N/A'}"
        )
        if r.student_work_steps:
            entry += f"\n  Work steps:\n"
            for j, step in enumerate(r.student_work_steps, 1):
                entry += f"    Step {j}: {step}\n"
        responses_text.append(entry)

    skills_text = "\n".join(
        f"  - {s.name} (difficulty {s.difficulty})" for s in case.available_skills
    ) or "  (none provided)"

    misconceptions_text = "\n".join(
        f"  - [{m.related_skill_name}] {m.description}"
        for m in case.available_misconceptions
    ) or "  (none provided)"

    diag_text = "\n".join(
        f"  Q{d.question_id}: {d.question_content} → Student: {d.student_answer} "
        f"(correct: {d.is_correct}, sig: {d.error_signature or 'N/A'})"
        for d in case.diagnostic_history
    ) or "  (none)"

    return f"""\
STUDENT CASE

Student responses:
{chr(10).join(responses_text)}

Available skills:
{skills_text}

Available misconceptions:
{misconceptions_text}

Diagnostic questions asked so far:
{diag_text}

Produce your independent diagnosis now."""


# ── Call 2 — Comparison ───────────────────────────────────────────────

COMPARISON_SYSTEM = """\
You have already produced an independent diagnosis of a student's root cause.

Now you will receive the prediction made by the Adaptive Diagnostic Engine.

Compare your independent diagnosis against the engine's prediction.
Determine whether the engine's root cause is:
- SUPPORTED: correctly supported by evidence
- PARTIALLY_SUPPORTED: plausible but insufficiently supported
- UNSUPPORTED: incorrect given the evidence
- INSUFFICIENT_EVIDENCE: impossible to determine from available evidence

Be rigorous. Do not be agreeable.
The purpose is to discover failures in the diagnostic engine, not to validate it.

Identify the single biggest weakness in the engine's diagnostic reasoning, if one exists.

Return your comparison as a JSON object with exactly this structure:
{
  "engine_root_cause": "...",
  "independent_root_cause": "...",
  "agreement": true,
  "diagnostic_quality": "supported | partially_supported | unsupported | insufficient_evidence",
  "engine_confidence_supported": true,
  "major_issue": "...",
  "recommendation": "..."
}

Return ONLY valid JSON."""


def build_comparison_prompt(
    independent: IndependentDiagnosis,
    engine: EnginePrediction,
) -> str:
    """Build the user-message for Call 2."""
    return f"""\
YOUR INDEPENDENT DIAGNOSIS (already completed):
{json.dumps(independent.model_dump(), indent=2, default=str)}

ENGINE PREDICTION (revealed now):
  Root cause: {engine.root_cause}
  Confidence: {engine.confidence}
  Detail: {engine.diagnosis_detail or 'N/A'}

Compare your independent diagnosis with the engine prediction now."""
