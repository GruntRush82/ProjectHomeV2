"""Unit tests for the multiplication mission handler."""

import pytest

from app.models.mission import Mission, MissionAssignment, MissionProgress
from app.services.missions.multiplication import (
    CANONICAL_FACTS,
    MultiplicationHandler,
    _analyze_history,
    _canonical_key,
    _select_questions,
    get_mnemonic,
)


@pytest.fixture
def handler():
    return MultiplicationHandler()


@pytest.fixture
def mult_mission(app, db):
    m = Mission(
        title="Multiplication Master",
        description="Master multiplication",
        mission_type="multiplication",
        config={"range_min": 1, "range_max": 12},
        reward_cash=50.0,
        reward_icon="lightning_brain",
    )
    db.session.add(m)
    db.session.commit()
    return m


@pytest.fixture
def mult_assignment(app, db, mult_mission, sample_users):
    a = MissionAssignment(
        mission_id=mult_mission.id,
        user_id=sample_users["kid1"].id,
    )
    db.session.add(a)
    db.session.commit()
    return a


class TestCanonicalFacts:
    def test_canonical_facts_count(self):
        assert len(CANONICAL_FACTS) == 78

    def test_canonical_facts_no_duplicates(self):
        assert len(set(CANONICAL_FACTS)) == 78

    def test_canonical_key(self):
        assert _canonical_key(3, 7) == (3, 7)
        assert _canonical_key(7, 3) == (3, 7)
        assert _canonical_key(5, 5) == (5, 5)

    def test_all_facts_have_a_le_b(self):
        for a, b in CANONICAL_FACTS:
            assert a <= b


class TestMnemonics:
    def test_known_mnemonic(self):
        hint = get_mnemonic(6, 7)
        assert "forty-two" in hint.lower() or "42" in hint

    def test_reversed_args_same_mnemonic(self):
        assert get_mnemonic(7, 6) == get_mnemonic(6, 7)

    def test_default_mnemonic(self):
        hint = get_mnemonic(2, 3)
        assert "6" in hint  # 2*3=6 in "say it three times"

    def test_hard_facts_have_mnemonics(self):
        hard_facts = [(7, 8), (8, 8), (9, 9), (6, 7)]
        for a, b in hard_facts:
            hint = get_mnemonic(a, b)
            assert "three times" not in hint  # should have a custom one


class TestAnalyzeHistory:
    def test_empty_history(self, app, db, mult_assignment):
        mastered, weak, unseen = _analyze_history([])
        assert len(unseen) == 78
        assert len(mastered) == 0
        assert len(weak) == 0

    def test_mastered_classification(self, app, db, mult_assignment):
        """A fact seen 3+ times with 80%+ accuracy is mastered."""
        questions = [
            {"a": 2, "b": 3, "correct": True},
            {"a": 2, "b": 3, "correct": True},
            {"a": 2, "b": 3, "correct": True},
        ]
        p = MissionProgress(
            assignment_id=mult_assignment.id,
            session_type="training",
            data={"questions": questions},
            score=3,
        )
        db.session.add(p)
        db.session.commit()

        mastered, weak, unseen = _analyze_history([p])
        assert (2, 3) in mastered
        assert (2, 3) not in weak
        assert (2, 3) not in unseen

    def test_weak_classification(self, app, db, mult_assignment):
        """A fact with < 80% accuracy is weak."""
        questions = [
            {"a": 6, "b": 7, "correct": True},
            {"a": 6, "b": 7, "correct": False},
            {"a": 6, "b": 7, "correct": False},
        ]
        p = MissionProgress(
            assignment_id=mult_assignment.id,
            session_type="training",
            data={"questions": questions},
            score=1,
        )
        db.session.add(p)
        db.session.commit()

        mastered, weak, unseen = _analyze_history([p])
        assert (6, 7) in weak
        assert (6, 7) not in mastered


class TestQuestionSelection:
    def test_returns_requested_count(self):
        mastered = set(CANONICAL_FACTS[:20])
        weak = set(CANONICAL_FACTS[20:30])
        unseen = set(CANONICAL_FACTS[30:])
        questions = _select_questions(mastered, weak, unseen, count=20)
        assert len(questions) == 20

    def test_all_questions_valid(self):
        questions = _select_questions(set(), set(), set(CANONICAL_FACTS), count=20)
        for q in questions:
            assert 1 <= q["a"] <= 12
            assert 1 <= q["b"] <= 12
            assert q["answer"] == q["a"] * q["b"]

    def test_weak_facts_prioritized(self):
        """When weak facts exist, they should appear frequently."""
        weak = {(6, 7), (7, 8), (8, 9)}
        mastered = set(CANONICAL_FACTS[:50]) - weak
        unseen = set(CANONICAL_FACTS[50:]) - weak
        questions = _select_questions(mastered, weak, unseen, count=20)
        weak_questions = sum(
            1 for q in questions
            if _canonical_key(q["a"], q["b"]) in weak
        )
        # With 50% target weight for weak, we expect significant representation
        assert weak_questions >= 3


class TestTrainingSession:
    def test_get_training_session(self, app, db, handler, mult_assignment):
        session = handler.get_training_session(mult_assignment)
        assert session["type"] == "training"
        assert len(session["questions"]) == 20
        assert session["total"] == 20
        for q in session["questions"]:
            assert "a" in q and "b" in q

    def test_evaluate_training_records_progress(self, app, db, handler, mult_assignment):
        questions = [
            {"a": 2, "b": 3, "user_answer": 6, "correct": True},
            {"a": 4, "b": 5, "user_answer": 20, "correct": True},
            {"a": 6, "b": 7, "user_answer": 40, "correct": False},
        ]
        result = handler.evaluate_training(mult_assignment, {
            "questions": questions,
            "duration_seconds": 60,
        })

        assert result["correct"] == 2
        assert result["total"] == 3
        assert result["total_facts"] == 78

        # Should have recorded progress
        progress = MissionProgress.query.filter_by(
            assignment_id=mult_assignment.id
        ).all()
        assert len(progress) == 1

    def test_training_transitions_from_assigned(self, app, db, handler, mult_assignment):
        assert mult_assignment.state == "assigned"
        handler.evaluate_training(mult_assignment, {"questions": [], "duration_seconds": 0})
        assert mult_assignment.state == "training"
        assert mult_assignment.started_at is not None

    def test_training_transitions_from_failed(self, app, db, handler, mult_assignment):
        mult_assignment.state = MissionAssignment.STATE_FAILED
        db.session.commit()
        handler.evaluate_training(mult_assignment, {"questions": [], "duration_seconds": 0})
        assert mult_assignment.state == "training"


class TestMultiplicationTest:
    def test_get_test_returns_questions(self, app, db, handler, mult_assignment):
        test = handler.get_test(mult_assignment, level=1)
        assert test["type"] == "test"
        assert test["level"] == 1
        assert len(test["questions"]) == 45
        assert test["time_limit"] is None

    def test_get_test_level2_has_time_limit(self, app, db, handler, mult_assignment):
        test = handler.get_test(mult_assignment, level=2)
        assert test["time_limit"] == 120

    def test_get_test_level3_has_time_limit(self, app, db, handler, mult_assignment):
        test = handler.get_test(mult_assignment, level=3)
        assert test["time_limit"] == 60

    def test_pass_level1(self, app, db, handler, mult_assignment):
        test = handler.get_test(mult_assignment, level=1)
        questions = test["questions"]
        answers = [q["a"] * q["b"] for q in questions]

        result = handler.evaluate_test(mult_assignment, {
            "level": 1,
            "answers": answers,
            "questions": questions,
            "duration_seconds": 300,
        })

        assert result["passed"] is True
        assert result["level"] == 1
        assert mult_assignment.current_level == 1
        assert mult_assignment.state != MissionAssignment.STATE_COMPLETED

    def test_pass_level3_completes_mission(self, app, db, handler, mult_assignment):
        mult_assignment.current_level = 2
        mult_assignment.state = MissionAssignment.STATE_TRAINING
        db.session.commit()

        test = handler.get_test(mult_assignment, level=3)
        questions = test["questions"]
        answers = [q["a"] * q["b"] for q in questions]

        result = handler.evaluate_test(mult_assignment, {
            "level": 3,
            "answers": answers,
            "questions": questions,
            "duration_seconds": 55,  # within 60s limit
        })

        assert result["passed"] is True
        assert result["completed"] is True
        assert mult_assignment.state == MissionAssignment.STATE_COMPLETED
        assert mult_assignment.completed_at is not None

    def test_fail_wrong_answers(self, app, db, handler, mult_assignment):
        test = handler.get_test(mult_assignment, level=1)
        questions = test["questions"]
        answers = [0] * len(questions)  # all wrong

        result = handler.evaluate_test(mult_assignment, {
            "level": 1,
            "answers": answers,
            "questions": questions,
            "duration_seconds": 60,
        })

        assert result["passed"] is False
        assert mult_assignment.state == MissionAssignment.STATE_FAILED

    def test_fail_time_limit_exceeded(self, app, db, handler, mult_assignment):
        test = handler.get_test(mult_assignment, level=2)
        questions = test["questions"]
        answers = [q["a"] * q["b"] for q in questions]  # all correct

        result = handler.evaluate_test(mult_assignment, {
            "level": 2,
            "answers": answers,
            "questions": questions,
            "duration_seconds": 200,  # exceeds 120s limit
        })

        assert result["passed"] is False
        assert "reason" in result


class TestProgressSummary:
    def test_empty_progress(self, app, db, handler, mult_assignment):
        summary = handler.get_progress_summary(mult_assignment)
        assert summary["mastered_count"] == 0
        assert summary["unseen_count"] == 78
        assert summary["training_sessions"] == 0
        assert summary["current_level"] == 0
