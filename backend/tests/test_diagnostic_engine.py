import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.domain import Question
from app.services.diagnostic_engine import DiagnosticEngine
from app.services.question_selector import QuestionSelector
from app.models.student import DiagnosticSession

# Setup an in-memory SQLite for isolated tests
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def seed_test_questions(db):
    dp1 = {"tests": ["skill1"], "outcomes": {"err1": {"supports": ["H1"]}, "correct": {"weakens": ["H1"]}}}
    q1 = Question(id=1, content="Q1", structural_family="F1", diagnostic_properties=dp1)
    
    dp2 = {"tests": ["skill2"], "outcomes": {"err2": {"supports": ["H2"]}, "correct": {"weakens": ["H2"]}}}
    q2 = Question(id=2, content="Q2", structural_family="F2", diagnostic_properties=dp2)
    
    # Q3 strongly discriminates H1 vs H2
    dp3 = {"tests": ["skill3"], "outcomes": {"err3": {"supports": ["H1"], "weakens": ["H2"]}, "correct": {"supports": ["H2"], "weakens": ["H1"]}}}
    q3 = Question(id=3, content="Q3", structural_family="F3", diagnostic_properties=dp3)
    
    # Q4 is structurally similar to Q1
    q4 = Question(id=4, content="Q4", structural_family="F1", diagnostic_properties=dp1)

    db.add_all([q1, q2, q3, q4])
    db.commit()

# Test 1 — No Repetition
def test_no_repetition(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    
    q_first = engine.select_next_question(sess)
    assert q_first is not None
    
    # Verify it doesn't pick it again
    q_second = engine.select_next_question(sess)
    assert q_second.id != q_first.id

# Test 2 — Information-Gain Selection
def test_ig_selection(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    # Force tied hypotheses
    sess.hypotheses = {"H1": 0.4, "H2": 0.4, "H3": 0.2}
    db_session.commit()
    
    q = engine.select_next_question(sess)
    # Q3 discriminates H1 and H2 best
    assert q.id == 3

# Test 3 — Hypothesis-Sensitive Selection
def test_hypothesis_sensitive_selection(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    
    # If H2 is very likely, a question targeting H2 might be selected
    sess.hypotheses = {"H1": 0.1, "H2": 0.8, "H3": 0.1}
    db_session.commit()
    
    q = engine.select_next_question(sess)
    assert q.id == 2 or q.id == 3

# Test 4 — Structural Similarity
def test_structural_similarity(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    sess.hypotheses = {"H1": 0.5, "H2": 0.5}
    sess.asked_questions = [1] # Asked Q1 (Family F1)
    db_session.commit()
    
    # Q4 is also F1. It should have a penalty, so Q2 or Q3 should be preferred.
    q = engine.select_next_question(sess)
    assert q.id != 4

# Test 5 — Evidence Independence
def test_evidence_independence(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    sess.hypotheses = {"H1": 0.5, "H2": 0.5}
    db_session.commit()
    
    # 5 identical errors on structural family F1
    for _ in range(5):
        sess = engine.update_hypotheses(sess, 1, False, "err1")
        
    final_h1 = sess.hypotheses["H1"]
    
    # Reset
    sess2 = engine.initialize_session(2, 1, "initial")
    sess2.hypotheses = {"H1": 0.5, "H2": 0.5}
    db_session.commit()
    
    # 5 errors on DIFFERENT families (mocking different questions targeting H1)
    sess2 = engine.update_hypotheses(sess2, 1, False, "err1")
    sess2 = engine.update_hypotheses(sess2, 3, False, "err3") # Q3 supports H1
    
    # Compare
    # 2 diverse strong supports should yield higher confidence than 5 identical repeated ones.
    assert final_h1 < sess2.hypotheses["H1"]

# Test 6 — Contradictory Evidence
def test_contradictory_evidence(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    sess.hypotheses = {"H1": 0.5, "H2": 0.5}
    
    # Support H1
    sess = engine.update_hypotheses(sess, 1, False, "err1")
    prob_after_support = sess.hypotheses["H1"]
    assert prob_after_support > 0.5
    
    # Contradict H1 (get Q1 correct)
    sess = engine.update_hypotheses(sess, 1, True, "correct")
    prob_after_contradict = sess.hypotheses["H1"]
    assert prob_after_contradict < prob_after_support

# Test 7 — Hypothesis Elimination
def test_hypothesis_elimination(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    sess.hypotheses = {"H1": 0.5, "H2": 0.5}
    
    # Strong contradiction
    for _ in range(3):
        sess = engine.update_hypotheses(sess, 1, True, "correct")
        
    assert sess.hypotheses["H1"] < 0.1

# Test 8 — Termination
def test_termination(db_session):
    seed_test_questions(db_session)
    engine = DiagnosticEngine(db_session)
    sess = engine.initialize_session(1, 1, "initial")
    sess.hypotheses = {"H1": 0.5, "H2": 0.5}
    db_session.commit()
    
    for i in range(5):
        sess.asked_questions = sess.asked_questions + [i]
        sess = engine.update_hypotheses(sess, 1, False, "unknown")
        
    assert sess.status == "completed"
    assert sess.diagnosis["primary_cause"] == "INSUFFICIENT_EVIDENCE"
    assert sess.confidence < 0.8

# Test 9 — Information Gain Determinism
def test_ig_determinism(db_session):
    seed_test_questions(db_session)
    selector = QuestionSelector()
    sess = DiagnosticSession(hypotheses={"H1": 0.5, "H2": 0.5}, asked_questions=[])
    questions = db_session.query(Question).all()
    
    q1, r1 = selector.select_next_question(sess, questions)
    q2, r2 = selector.select_next_question(sess, questions)
    
    assert q1.id == q2.id
    assert r1["expected_information_gain"] == r2["expected_information_gain"]

# Test 10 — Isolation
def test_isolation():
    # DiagnosticEngine only accepts primitive IDs and Error Signatures.
    # It does not accept SyntheticStudentProfile.
    import inspect
    sig = inspect.signature(DiagnosticEngine.update_hypotheses)
    assert "profile" not in sig.parameters
    assert "ground_truth" not in sig.parameters
