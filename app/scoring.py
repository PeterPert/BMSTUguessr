from __future__ import annotations

import math

FLOOR_PENALTY_METERS = 15.0
DEFAULT_METERS_PER_PIXEL = 0.1


def calculate_distance_meters(
    answer_x: int,
    answer_y: int,
    answer_floor: int,
    guessed_x: int,
    guessed_y: int,
    guessed_floor: int,
    meters_per_pixel: float = DEFAULT_METERS_PER_PIXEL,
) -> float:
    pixel_distance = math.hypot(answer_x - guessed_x, answer_y - guessed_y)
    horizontal = pixel_distance * meters_per_pixel
    vertical_penalty = FLOOR_PENALTY_METERS * abs(answer_floor - guessed_floor)
    return horizontal + vertical_penalty


def points_for_distance(distance_meters: float) -> int:
    if distance_meters < 5:
        return 5
    if distance_meters < 10:
        return 4
    if distance_meters < 20:
        return 3
    if distance_meters < 30:
        return 2
    if distance_meters < 40:
        return 1
    return 0
