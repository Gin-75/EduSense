"""
Question Selector Service.

Selects the next best diagnostic question using Information Gain.
Reads P(outcome | hypothesis) likelihoods from question metadata.
"""
import math
from typing import List, Dict, Any, Tuple
from app.models.domain import Question
from app.models.student import DiagnosticSession


class QuestionSelector:
    def __init__(self, lambda_penalty: float = 0.05):
        self.lambda_penalty = lambda_penalty

    def select_next_question(
        self,
        session: DiagnosticSession,
        available_questions: List[Question],
    ) -> Tuple[Question, Dict[str, Any]]:
        """Returns the selected question and the rationale metadata."""
        hypotheses = session.hypotheses
        if not hypotheses:
            candidates = [
                q for q in available_questions if q.id not in session.asked_questions
            ]
            if not candidates:
                return None, {}
            return candidates[0], {"selection_reason": "fallback_no_hypotheses"}

        current_entropy = self._calculate_entropy(list(hypotheses.values()))

        # Build history of structural families already asked
        asked_families = []
        for q in available_questions:
            if q.id in session.asked_questions and q.structural_family:
                asked_families.append(q.structural_family)

        best_q = None
        best_score = -float("inf")
        best_rationale = {}

        for q in available_questions:
            if q.id in session.asked_questions:
                continue

            ig = self._calculate_expected_ig(hypotheses, q, current_entropy)

            # Structural similarity penalty
            penalty = 0.0
            if q.structural_family in asked_families:
                count = asked_families.count(q.structural_family)
                penalty = self.lambda_penalty * count

            effective_score = ig - penalty

            if effective_score > best_score:
                best_score = effective_score
                best_q = q
                best_rationale = {
                    "question_id": q.id,
                    "expected_information_gain": ig,
                    "structural_similarity_penalty": penalty,
                    "effective_score": effective_score,
                    "selection_reason": "highest_expected_information_gain",
                    "hypotheses_before": hypotheses.copy(),
                }

        if not best_q:
            candidates = [
                q for q in available_questions if q.id not in session.asked_questions
            ]
            if not candidates:
                return None, {}
            return candidates[0], {"selection_reason": "fallback_no_candidates"}

        return best_q, best_rationale

    def _calculate_entropy(self, probs: List[float]) -> float:
        return -sum(p * math.log2(p) for p in probs if p > 1e-9)

    def _calculate_expected_ig(
        self,
        hypotheses: Dict[str, float],
        q: Question,
        current_entropy: float,
    ) -> float:
        dp = q.diagnostic_properties
        if not dp or "outcomes" not in dp:
            return 0.0

        outcomes = dp["outcomes"]

        # Build P(outcome | hypothesis) table from metadata
        likelihoods: Dict[str, Dict[str, float]] = {}
        for outcome, rules in outcomes.items():
            likelihoods[outcome] = {}
            outcome_lk = rules.get("likelihoods", None)

            if outcome_lk:
                # New format: read likelihoods directly
                for h in hypotheses:
                    likelihoods[outcome][h] = outcome_lk.get(h, 0.1)
            else:
                # Legacy format: heuristic likelihoods from supports/weakens
                supports = rules.get("supports", [])
                weakens = rules.get("weakens", [])
                for h in hypotheses:
                    if h in supports:
                        likelihoods[outcome][h] = 0.8
                    elif h in weakens:
                        likelihoods[outcome][h] = 0.1
                    else:
                        likelihoods[outcome][h] = 0.4

        # Normalize P(o|h) so they sum to 1.0 for each h
        for h in hypotheses:
            total_lh = sum(likelihoods[o][h] for o in outcomes)
            if total_lh > 0:
                for o in outcomes:
                    likelihoods[o][h] /= total_lh

        # Expected entropy after asking this question
        expected_entropy = 0.0
        for outcome in outcomes:
            # P(outcome) = sum_h P(outcome|h) * P(h)
            p_outcome = sum(
                likelihoods[outcome][h] * prob for h, prob in hypotheses.items()
            )

            if p_outcome > 1e-9:
                # P(h|outcome) = P(outcome|h) * P(h) / P(outcome)
                posterior = []
                for h, prob in hypotheses.items():
                    p_h_given_o = (likelihoods[outcome][h] * prob) / p_outcome
                    posterior.append(p_h_given_o)

                h_given_o = self._calculate_entropy(posterior)
                expected_entropy += p_outcome * h_given_o

        ig = current_entropy - expected_entropy
        return max(0.0, ig)
