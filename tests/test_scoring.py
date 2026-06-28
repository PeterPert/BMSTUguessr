"""Tests for app.scoring — distance calculation and point assignment."""

from __future__ import annotations

import math

import pytest

from app.scoring import (
    DEFAULT_METERS_PER_PIXEL,
    FLOOR_PENALTY_METERS,
    calculate_distance_meters,
    points_for_distance,
)


class TestCalculateDistanceMeters:
    """Tests for calculate_distance_meters()."""

    def test_exact_match_same_floor(self):
        """Exact same coordinates and floor → 0 meters."""
        result = calculate_distance_meters(100, 200, 3, 100, 200, 3)
        assert result == 0.0

    def test_horizontal_distance_only(self):
        """Same floor, different coordinates → Euclidean * scale."""
        result = calculate_distance_meters(0, 0, 1, 30, 40, 1)
        expected = math.hypot(30, 40) * DEFAULT_METERS_PER_PIXEL  # 50 * 0.1 = 5.0
        assert result == pytest.approx(expected)

    def test_floor_penalty_only(self):
        """Same coordinates, different floors → pure penalty."""
        result = calculate_distance_meters(500, 300, 2, 500, 300, 5)
        assert result == pytest.approx(FLOOR_PENALTY_METERS * 3)

    def test_combined_distance_and_penalty(self):
        """Both horizontal offset and wrong floor."""
        result = calculate_distance_meters(0, 0, 1, 30, 40, 3)
        horizontal = math.hypot(30, 40) * DEFAULT_METERS_PER_PIXEL
        penalty = FLOOR_PENALTY_METERS * 2
        assert result == pytest.approx(horizontal + penalty)

    def test_custom_scale(self):
        """Respects custom meters_per_pixel parameter."""
        result = calculate_distance_meters(0, 0, 1, 10, 0, 1, meters_per_pixel=0.5)
        assert result == pytest.approx(5.0)

    def test_symmetry(self):
        """Distance is the same regardless of direction."""
        d1 = calculate_distance_meters(0, 0, 1, 100, 100, 3)
        d2 = calculate_distance_meters(100, 100, 3, 0, 0, 1)
        assert d1 == pytest.approx(d2)


class TestPointsForDistance:
    """Tests for points_for_distance()."""

    def test_perfect_5_stars(self):
        assert points_for_distance(0.0) == 5
        assert points_for_distance(4.99) == 5

    def test_4_stars(self):
        assert points_for_distance(5.0) == 4
        assert points_for_distance(9.99) == 4

    def test_3_stars(self):
        assert points_for_distance(10.0) == 3
        assert points_for_distance(19.99) == 3

    def test_2_stars(self):
        assert points_for_distance(20.0) == 2
        assert points_for_distance(29.99) == 2

    def test_1_star(self):
        assert points_for_distance(30.0) == 1
        assert points_for_distance(39.99) == 1

    def test_0_stars(self):
        assert points_for_distance(40.0) == 0
        assert points_for_distance(999.0) == 0

    def test_boundary_values(self):
        """Each boundary falls into the correct bucket."""
        boundaries = [(5, 4), (10, 3), (20, 2), (30, 1), (40, 0)]
        for dist, expected in boundaries:
            assert points_for_distance(dist) == expected, f"Failed at {dist}m"
