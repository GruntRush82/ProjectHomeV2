"""Unit tests for allowance tier calculation."""

from app.services.allowance import calculate_allowance


class TestCalculateAllowance:
    """Tests for the 100/50/0 tier rule."""

    def test_full_completion_gets_full_allowance(self):
        assert calculate_allowance(10, 10, 15.0) == 15.0

    def test_half_completion_gets_half_allowance(self):
        assert calculate_allowance(10, 5, 15.0) == 7.5

    def test_above_half_gets_half_allowance(self):
        assert calculate_allowance(10, 7, 15.0) == 7.5

    def test_below_half_gets_zero(self):
        assert calculate_allowance(10, 4, 15.0) == 0.0

    def test_zero_completion_gets_zero(self):
        assert calculate_allowance(10, 0, 15.0) == 0.0

    def test_no_chores_gets_zero(self):
        assert calculate_allowance(0, 0, 15.0) == 0.0

    def test_exactly_50_percent_gets_half(self):
        assert calculate_allowance(4, 2, 20.0) == 10.0

    def test_one_chore_complete_gets_full(self):
        assert calculate_allowance(1, 1, 100.0) == 100.0

    def test_one_chore_incomplete_gets_zero(self):
        assert calculate_allowance(1, 0, 100.0) == 0.0

    def test_odd_allowance_rounds_correctly(self):
        # $15 * 0.5 = $7.50
        assert calculate_allowance(10, 5, 15.0) == 7.5
