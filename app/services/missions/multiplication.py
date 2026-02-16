"""Multiplication mission handler.

Training: adaptive sessions with 20 questions, weighted toward weak facts.
Testing: 3 levels (L1 untimed, L2 120s, L3 60s), 45 correct required.
"""

import random
from datetime import datetime

from app.extensions import db
from app.models.mission import MissionAssignment, MissionProgress
from app.services.missions.base import BaseMissionHandler

# 78 canonical facts: (a, b) where a <= b, both in 1..12
CANONICAL_FACTS = [
    (a, b) for a in range(1, 13) for b in range(a, 13)
]

# Mnemonic hints for commonly-hard facts
MNEMONICS = {
    (6, 7): "Six times seven is forty-two — the answer to everything!",
    (6, 8): "Six and eight went on a date — the answer is forty-eight!",
    (7, 8): "Seven ate (8) fifty-six — 7 x 8 = 56!",
    (8, 8): "I ate and I ate till I was sick on the floor — 8 x 8 = 64!",
    (6, 9): "If 6 times 10 is 60, take away one 6 — that's 54!",
    (7, 9): "7 x 9: the digits add to 9 and start with 6 — 63!",
    (8, 9): "8 x 9: the digits add to 9 and start with 7 — 72!",
    (9, 9): "9 x 9: the digits add to 9 and start with 8 — 81!",
    (7, 7): "Seven touchdown! 7 x 7 = 49!",
    (4, 7): "4 x 7 = 28 — there are 28 days in February!",
    (3, 7): "3 weeks = 21 days — 3 x 7 = 21!",
    (6, 6): "6 x 6 = 36 — three dozen and six!",
    (8, 12): "8 x 12 = 96 — almost 100!",
    (7, 12): "7 x 12 = 84 — seven dozen!",
    (9, 12): "9 x 12 = 108 — just over 100!",
    (11, 12): "11 x 12 = 132 — eleven dozen!",
    (12, 12): "12 x 12 = 144 — a gross! That's a dozen dozen!",
}

DEFAULT_MNEMONIC = "Say the answer three times: {answer}, {answer}, {answer}. Now you've got it!"

# Test level configuration
LEVELS = {
    1: {"time_limit": None, "questions": 45},
    2: {"time_limit": 120, "questions": 45},
    3: {"time_limit": 60, "questions": 45},
}


def _canonical_key(a, b):
    """Return the canonical (min, max) tuple for a fact."""
    return (min(a, b), max(a, b))


def _get_mnemonic(a, b):
    """Return a mnemonic hint for a fact, or the default."""
    key = _canonical_key(a, b)
    hint = MNEMONICS.get(key)
    if hint:
        return hint
    answer = a * b
    return DEFAULT_MNEMONIC.format(answer=answer)


def _analyze_history(progress_records, last_n=3):
    """Analyze the last N training sessions to classify facts.

    Returns:
        mastered: set of canonical (a, b) tuples with >= 80% accuracy and >= 3 attempts
        weak: set of canonical tuples with < 80% accuracy
        unseen: set of canonical tuples not yet attempted
    """
    # Collect attempts from last N training sessions
    training_records = [
        r for r in progress_records
        if r.session_type == "training"
    ]
    recent = training_records[:last_n]  # already sorted desc by created_at

    attempts = {}  # canonical_key -> {"correct": int, "total": int}
    for record in recent:
        data = record.data or {}
        for q in data.get("questions", []):
            key = _canonical_key(q["a"], q["b"])
            if key not in attempts:
                attempts[key] = {"correct": 0, "total": 0}
            attempts[key]["total"] += 1
            if q.get("correct"):
                attempts[key]["correct"] += 1

    mastered = set()
    weak = set()
    unseen = set()

    for fact in CANONICAL_FACTS:
        if fact not in attempts:
            unseen.add(fact)
        elif attempts[fact]["total"] >= 3 and (attempts[fact]["correct"] / attempts[fact]["total"]) >= 0.8:
            mastered.add(fact)
        else:
            weak.add(fact)

    return mastered, weak, unseen


def _select_questions(mastered, weak, unseen, count=20):
    """Select questions with adaptive weighting.

    If weak facts exist: 50% weak, 30% unseen, 20% mastered.
    Adjusts when a category is empty. No repeat within 3 questions.
    """
    # Calculate target counts based on availability
    pools = {"weak": list(weak), "unseen": list(unseen), "mastered": list(mastered)}

    # Default weights
    weights = {"weak": 0.5, "unseen": 0.3, "mastered": 0.2}

    # Adjust if categories are empty
    if not pools["weak"]:
        weights["weak"] = 0
        if pools["unseen"]:
            weights["unseen"] += 0.3
            weights["mastered"] += 0.2
        else:
            weights["mastered"] = 1.0
    if not pools["unseen"]:
        weights["unseen"] = 0
        if pools["weak"]:
            weights["weak"] += 0.15
            weights["mastered"] += 0.15
        else:
            weights["mastered"] = 1.0 - weights["weak"]
    if not pools["mastered"]:
        weights["mastered"] = 0
        remaining = 1.0 - weights["weak"] - weights["unseen"]
        if pools["weak"] and pools["unseen"]:
            weights["weak"] += remaining / 2
            weights["unseen"] += remaining / 2
        elif pools["weak"]:
            weights["weak"] += remaining
        elif pools["unseen"]:
            weights["unseen"] += remaining

    # Normalize
    total_w = sum(weights.values())
    if total_w > 0:
        weights = {k: v / total_w for k, v in weights.items()}

    questions = []
    recent_keys = []  # last 3 canonical keys used

    for _ in range(count):
        # Pick a category based on weights
        categories = [c for c in ["weak", "unseen", "mastered"] if pools[c]]
        if not categories:
            # All pools exhausted — refill from all facts
            pools = {"weak": list(weak), "unseen": list(unseen), "mastered": list(mastered)}
            categories = [c for c in ["weak", "unseen", "mastered"] if pools[c]]
            if not categories:
                # No facts at all (shouldn't happen)
                break

        cat_weights = [weights.get(c, 0) for c in categories]
        total_cw = sum(cat_weights)
        if total_cw == 0:
            cat_weights = [1.0 / len(categories)] * len(categories)
        else:
            cat_weights = [w / total_cw for w in cat_weights]

        chosen_cat = random.choices(categories, weights=cat_weights, k=1)[0]
        pool = pools[chosen_cat]

        # Pick a fact not in recent_keys
        available = [f for f in pool if f not in recent_keys]
        if not available:
            available = pool  # relax constraint

        fact = random.choice(available)

        # Present in random order (a*b or b*a)
        a, b = fact
        if a != b and random.random() < 0.5:
            a, b = b, a

        questions.append({"a": a, "b": b, "answer": a * b})

        # Track recent to avoid repeats
        recent_keys.append(_canonical_key(a, b))
        if len(recent_keys) > 3:
            recent_keys.pop(0)

        # Remove from pool so we don't over-sample one fact
        if fact in pool:
            pool.remove(fact)

    return questions


class MultiplicationHandler(BaseMissionHandler):
    """Handler for the Multiplication Master mission."""

    def get_training_session(self, assignment):
        """Generate a 20-question adaptive training session."""
        mastered, weak, unseen = _analyze_history(assignment.progress_records)
        questions = _select_questions(mastered, weak, unseen, count=20)

        return {
            "type": "training",
            "questions": [{"a": q["a"], "b": q["b"]} for q in questions],
            "answers": {f"{q['a']}x{q['b']}": q["answer"] for q in questions},
            "total": len(questions),
            "mastered_count": len(mastered),
            "weak_count": len(weak),
            "unseen_count": len(unseen),
        }

    def evaluate_training(self, assignment, results):
        """Process training results and record progress.

        Args:
            results: {
                "questions": [{"a": int, "b": int, "user_answer": int, "correct": bool}, ...],
                "duration_seconds": int
            }
        """
        questions = results.get("questions", [])
        duration = results.get("duration_seconds")

        correct = sum(1 for q in questions if q.get("correct"))
        total = len(questions)
        score_pct = (correct / total * 100) if total > 0 else 0

        # Record progress
        progress = MissionProgress(
            assignment_id=assignment.id,
            session_type="training",
            data={"questions": questions},
            score=correct,
            duration_seconds=duration,
        )
        db.session.add(progress)

        # Ensure state is training
        if assignment.state == MissionAssignment.STATE_ASSIGNED:
            assignment.state = MissionAssignment.STATE_TRAINING
            assignment.started_at = datetime.utcnow()
        elif assignment.state == MissionAssignment.STATE_FAILED:
            assignment.state = MissionAssignment.STATE_TRAINING

        db.session.commit()

        # Recalculate mastery after this session
        mastered, weak, unseen = _analyze_history(assignment.progress_records)

        return {
            "correct": correct,
            "total": total,
            "score_pct": round(score_pct, 1),
            "mastered_count": len(mastered),
            "weak_count": len(weak),
            "unseen_count": len(unseen),
            "total_facts": len(CANONICAL_FACTS),
        }

    def get_test(self, assignment, level=None):
        """Generate a 45-question test for the given level.

        Answers are NOT included — validation is server-side only.
        """
        level = level or (assignment.current_level + 1)
        level = min(level, 3)

        level_config = LEVELS.get(level, LEVELS[1])

        # Generate 45 random facts (1-12 x 1-12)
        questions = []
        for _ in range(level_config["questions"]):
            a = random.randint(1, 12)
            b = random.randint(1, 12)
            questions.append({"a": a, "b": b})

        # Store answers server-side on the assignment for validation
        test_key = f"_test_answers_L{level}"

        return {
            "type": "test",
            "level": level,
            "questions": questions,
            "time_limit": level_config["time_limit"],
            "total": level_config["questions"],
            "label": f"Level {level}",
            # Server stores answers internally, not sent to client
            "_answers": [q["a"] * q["b"] for q in questions],
        }

    def evaluate_test(self, assignment, results):
        """Evaluate a test submission.

        Args:
            results: {
                "level": int,
                "answers": [int, ...],  # user's answers in order
                "duration_seconds": int,
                "questions": [{"a": int, "b": int}, ...]  # the questions that were asked
            }
        """
        level = results.get("level", 1)
        user_answers = results.get("answers", [])
        questions = results.get("questions", [])
        duration = results.get("duration_seconds")

        level_config = LEVELS.get(level, LEVELS[1])

        # Server-side validation: compute correct answers
        correct_answers = [q["a"] * q["b"] for q in questions]
        correct_count = sum(
            1 for ua, ca in zip(user_answers, correct_answers)
            if ua == ca
        )

        # Check pass conditions
        all_correct = correct_count >= level_config["questions"]
        time_ok = True
        if level_config["time_limit"] is not None and duration is not None:
            time_ok = duration <= level_config["time_limit"]

        passed = all_correct and time_ok

        # Record progress
        progress = MissionProgress(
            assignment_id=assignment.id,
            session_type="test",
            data={
                "level": level,
                "questions": questions,
                "user_answers": user_answers,
                "correct_count": correct_count,
                "passed": passed,
            },
            score=correct_count,
            duration_seconds=duration,
        )
        db.session.add(progress)

        if passed:
            assignment.current_level = level
            if level >= 3:
                assignment.state = MissionAssignment.STATE_COMPLETED
                assignment.completed_at = datetime.utcnow()
            else:
                # Stay in testing/training state for next level
                assignment.state = MissionAssignment.STATE_TRAINING
        else:
            assignment.state = MissionAssignment.STATE_FAILED

        db.session.commit()

        result = {
            "passed": passed,
            "level": level,
            "correct": correct_count,
            "total": level_config["questions"],
            "duration_seconds": duration,
            "time_limit": level_config["time_limit"],
            "current_level": assignment.current_level,
            "completed": assignment.state == MissionAssignment.STATE_COMPLETED,
        }

        if not passed:
            if not all_correct:
                result["reason"] = f"Got {correct_count} of {level_config['questions']} correct"
            else:
                result["reason"] = f"Took {duration}s but limit is {level_config['time_limit']}s"

        return result

    def get_progress_summary(self, assignment):
        """Return progress summary for the multiplication mission."""
        mastered, weak, unseen = _analyze_history(assignment.progress_records)

        training_sessions = [
            r for r in assignment.progress_records
            if r.session_type == "training"
        ]
        test_records = [
            r for r in assignment.progress_records
            if r.session_type == "test"
        ]

        # Accuracy from last 3 training sessions
        recent_training = training_sessions[:3]
        total_q = 0
        total_correct = 0
        for r in recent_training:
            data = r.data or {}
            for q in data.get("questions", []):
                total_q += 1
                if q.get("correct"):
                    total_correct += 1

        recent_accuracy = (total_correct / total_q * 100) if total_q > 0 else 0

        return {
            "mastered_count": len(mastered),
            "weak_count": len(weak),
            "unseen_count": len(unseen),
            "total_facts": len(CANONICAL_FACTS),
            "training_sessions": len(training_sessions),
            "test_attempts": len(test_records),
            "current_level": assignment.current_level,
            "recent_accuracy": round(recent_accuracy, 1),
        }


def get_mnemonic(a, b):
    """Public accessor for mnemonic hints."""
    return _get_mnemonic(a, b)
