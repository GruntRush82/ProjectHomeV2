"""Base mission handler — abstract interface for all mission types."""

from abc import ABC, abstractmethod


class BaseMissionHandler(ABC):
    """Abstract base class for mission handlers.

    Each mission type (multiplication, piano, etc.) implements this interface.
    """

    @abstractmethod
    def get_training_session(self, assignment):
        """Generate training content for this assignment.

        Returns a dict with training data (questions, instructions, etc.)
        """

    @abstractmethod
    def evaluate_training(self, assignment, results):
        """Process submitted training results.

        Args:
            assignment: MissionAssignment instance
            results: dict of training session results from the client

        Returns a dict with score, feedback, and progress info.
        """

    @abstractmethod
    def get_test(self, assignment, level=None):
        """Generate test content for the given level.

        Returns a dict with test data (questions without answers for client).
        """

    @abstractmethod
    def evaluate_test(self, assignment, results):
        """Process submitted test results.

        Args:
            assignment: MissionAssignment instance
            results: dict with answers and timing from the client

        Returns a dict with pass/fail, score, and state transition info.
        """

    @abstractmethod
    def get_progress_summary(self, assignment):
        """Return a summary of progress for this assignment.

        Returns a dict with mastered count, accuracy, sessions completed, etc.
        """
