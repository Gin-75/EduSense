from sqlalchemy.orm import Session
from app.models.student import DiagnosticSession
from app.models.domain import Question
from app.services.question_selector import QuestionSelector


class DiagnosticEngine:
    """
    Adaptive Diagnostic Engine using proper Bayesian updating.
    
    Hypotheses are aligned with what the simulator can actually test:
      - NO_SIGNIFICANT_WEAKNESS: Student is mostly correct (Strong archetype)
      - PROCEDURAL_GAP: Systematic wrong algebraic operations
      - COMPUTATIONAL_ERROR: Systematic arithmetic mistakes
      - CARELESS_ERROR: Random mixed errors at low-moderate rate
      - MULTIPLE_WEAKNESSES: Both procedural and computational errors
    
    Evidence is P(outcome | hypothesis) likelihoods stored in question metadata.
    """

    # Default likelihood for hypotheses not listed in a question's metadata.
    # Small value = "this outcome is unlikely if this hypothesis is true".
    DEFAULT_LIKELIHOOD = 0.1

    CONFIDENCE_THRESHOLD_HIGH = 0.8
    CONFIDENCE_THRESHOLD_GUESS = 0.4
    MAX_QUESTIONS = 20

    def __init__(self, db: Session):
        self.db = db
        self.selector = QuestionSelector(lambda_penalty=0.05)

    def initialize_session(
        self,
        student_id: int,
        initial_skill_id: int,
        initial_evidence: str = None,
        initial_question_id: int = None,
    ) -> DiagnosticSession:
        """
        Starts a diagnostic session with uniform priors over all hypotheses.
        If initial_evidence is provided, immediately performs a Bayesian update.
        """
        initial_hypotheses = {
            "NO_SIGNIFICANT_WEAKNESS": 1/8,
            "PROCEDURAL_GAP": 1/8,
            "COMPUTATIONAL_ERROR": 1/8,
            "CARELESS_ERROR": 1/8,
            "MULTIPLE_WEAKNESSES": 1/8,
            "MISCONCEPTION_power_rule": 1/8,
            "MISCONCEPTION_chain_rule": 1/8,
            "MISCONCEPTION_integration_c": 1/8,
        }

        session = DiagnosticSession(
            student_id=student_id,
            initial_skill_id=initial_skill_id,
            hypotheses=initial_hypotheses,
            attempts_history=[],
            asked_questions=[],
            hypothesis_history=[initial_hypotheses.copy()],
            selection_rationale=[],
            evidence_history=[],
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Consume initial evidence and mark the trigger question as asked
        if initial_evidence and initial_question_id:
            asked = list(session.asked_questions or [])
            asked.append(initial_question_id)
            session.asked_questions = asked
            session = self._bayesian_update(
                session, initial_question_id, initial_evidence
            )

        return session

    def select_next_question(self, session: DiagnosticSession) -> Question:
        """Selects the next question based on expected information gain."""
        available_questions = self.db.query(Question).all()
        selected_q, rationale = self.selector.select_next_question(
            session, available_questions
        )

        if selected_q:
            rationale_list = list(session.selection_rationale or [])
            rationale_list.append(rationale)
            session.selection_rationale = rationale_list

            asked_list = list(session.asked_questions or [])
            asked_list.append(selected_q.id)
            session.asked_questions = asked_list

            self.db.commit()

        return selected_q

    def process_answer(
        self,
        session: DiagnosticSession,
        question_id: int,
        outcome: str,
    ) -> DiagnosticSession:
        """
        Public entry point for processing an answer.
        `outcome` must be one of: correct, arithmetic_error, wrong_op_error, mixed_error
        """
        return self._bayesian_update(session, question_id, outcome)

    # ── Keep legacy interface for backward compatibility ──────────────
    def update_hypotheses(
        self,
        session: DiagnosticSession,
        question_id: int,
        is_correct: bool,
        error_signature: str = None,
    ) -> DiagnosticSession:
        """Legacy interface — routes to _bayesian_update."""
        outcome = "correct" if is_correct else (error_signature or "unknown")
        return self._bayesian_update(session, question_id, outcome)

    # ── Core Bayesian update ─────────────────────────────────────────
    def _bayesian_update(
        self, session: DiagnosticSession, question_id: int, outcome: str
    ) -> DiagnosticSession:
        """
        Proper Bayesian update: P(H|E) ∝ P(E|H) · P(H)
        
        Reads P(E|H) likelihoods directly from the question's diagnostic_properties.
        Falls back to legacy supports/weakens if likelihoods are absent.
        """
        hypotheses = session.hypotheses.copy()
        question = self.db.query(Question).filter(Question.id == question_id).first()

        if not question or not question.diagnostic_properties:
            return session

        dp = question.diagnostic_properties
        outcomes_meta = dp.get("outcomes", {})

        # Map the observed outcome to a key in the metadata
        outcome_key = self._resolve_outcome_key(outcome, outcomes_meta)

        rules = outcomes_meta.get(outcome_key, {})
        likelihoods = rules.get("likelihoods", None)

        if likelihoods:
            # ── New path: proper Bayesian update ──
            for h in hypotheses:
                lk = likelihoods.get(h, self.DEFAULT_LIKELIHOOD)
                hypotheses[h] *= lk
        else:
            # ── Legacy fallback: supports/weakens multipliers ──
            supports = rules.get("supports", [])
            weakens = rules.get("weakens", [])
            for h in hypotheses:
                if h in supports:
                    hypotheses[h] *= 2.5
                elif h in weakens:
                    hypotheses[h] *= 0.2

        # Normalize
        total = sum(hypotheses.values())
        if total > 0:
            for k in hypotheses:
                hypotheses[k] /= total

        session.hypotheses = hypotheses

        # Record history with bounds to prevent unbounded JSON growth
        h_history = list(session.hypothesis_history or [])
        h_history.append(hypotheses.copy())
        session.hypothesis_history = h_history[-10:] # Keep only last 10 states

        evidence_history = list(session.evidence_history or [])
        evidence_history.append({
            "outcome": outcome_key,
            "question_id": question_id,
            "structural_family": question.structural_family,
        })
        session.evidence_history = evidence_history

        # ── Stopping conditions ──
        max_prob = max(hypotheses.values()) if hypotheses else 0
        top_hypothesis = max(hypotheses, key=hypotheses.get)

        conf_history = list(session.confidence_history or [])
        conf_history.append(max_prob)
        session.confidence_history = conf_history

        if max_prob >= self.CONFIDENCE_THRESHOLD_HIGH:
            # High-confidence diagnosis
            session.status = "completed"
            session.diagnosis = {
                "primary_cause": top_hypothesis,
                "confidence_tier": "high",
            }
            session.confidence = max_prob

        elif len(session.asked_questions) >= self.MAX_QUESTIONS:
            session.status = "completed"
            if max_prob >= self.CONFIDENCE_THRESHOLD_GUESS:
                # Best-guess diagnosis
                session.diagnosis = {
                    "primary_cause": top_hypothesis,
                    "confidence_tier": "medium",
                }
            else:
                session.diagnosis = {
                    "primary_cause": "INSUFFICIENT_EVIDENCE",
                    "confidence_tier": "low",
                }
            session.confidence = max_prob

        self.db.commit()
        self.db.refresh(session)
        return session

    # ── Helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _resolve_outcome_key(outcome: str, outcomes_meta: dict) -> str:
        """Map an observed outcome string to a key in the question metadata."""
        if outcome in outcomes_meta:
            return outcome

        # Fuzzy matching for legacy evaluator output
        if "sign_error" in outcomes_meta and "sign" in outcome:
            return "sign_error"
        if "arithmetic_error" in outcomes_meta and "arithmetic" in outcome:
            return "arithmetic_error"
        if "wrong_op_error" in outcomes_meta and "operation" in outcome:
            return "wrong_op_error"
        if "mixed_error" in outcomes_meta and "mixed" in outcome:
            return "mixed_error"

        return outcome  # Return as-is; will result in empty rules (no-op)
