"""Approximate two-body heliocentric propagation utilities."""

from __future__ import annotations

import numpy as np

DEG_TO_RAD = np.pi / 180.0
EARTH_MEAN_MOTION_RAD_PER_DAY = 2 * np.pi / 365.256


def simulate_min_distances(
    clones: dict[str, np.ndarray],
    horizon_days: int,
    time_step_days: int,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Return clone minimum distances and closest-approach days."""
    times = np.arange(0, max(horizon_days, time_step_days) + time_step_days, time_step_days)
    min_distances = np.full(len(clones["a"]), np.inf)
    closest_days = np.zeros(len(clones["a"]))
    quantile_trace = {"day": [], "p05": [], "p50": [], "p95": []}
    for day in times:
        positions = asteroid_positions(clones, float(day))
        earth = earth_position(float(day))
        distances = np.linalg.norm(positions - earth, axis=1)
        improved = distances < min_distances
        closest_days[improved] = day
        min_distances = np.minimum(min_distances, distances)
        quantile_trace["day"].append(float(day))
        quantile_trace["p05"].append(float(np.quantile(distances, 0.05)))
        quantile_trace["p50"].append(float(np.quantile(distances, 0.50)))
        quantile_trace["p95"].append(float(np.quantile(distances, 0.95)))
    return (
        min_distances,
        closest_days,
        {key: np.asarray(value) for key, value in quantile_trace.items()},
    )


def baseline_min_distance(
    elements: dict[str, float],
    horizon_days: int,
    time_step_days: int,
) -> tuple[float, float]:
    """Return baseline minimum Earth-object distance and day."""
    clones = {
        key: np.asarray([value], dtype=float)
        for key, value in elements.items()
        if key in {"a", "e", "i", "om", "w", "ma", "n"}
    }
    distances, days, _trace = simulate_min_distances(clones, horizon_days, time_step_days)
    return float(distances[0]), float(days[0])


def asteroid_positions(clones: dict[str, np.ndarray], day: float) -> np.ndarray:
    """Compute heliocentric ecliptic positions for clone arrays."""
    a = clones["a"]
    e = clones["e"]
    mean_anomaly = np.deg2rad(clones["ma"] + clones["n"] * day)
    eccentric_anomaly = solve_kepler(mean_anomaly, e)
    x_orb = a * (np.cos(eccentric_anomaly) - e)
    y_orb = a * np.sqrt(np.maximum(0.0, 1 - e**2)) * np.sin(eccentric_anomaly)

    cos_om = np.cos(clones["om"] * DEG_TO_RAD)
    sin_om = np.sin(clones["om"] * DEG_TO_RAD)
    cos_i = np.cos(clones["i"] * DEG_TO_RAD)
    sin_i = np.sin(clones["i"] * DEG_TO_RAD)
    cos_w = np.cos(clones["w"] * DEG_TO_RAD)
    sin_w = np.sin(clones["w"] * DEG_TO_RAD)

    x1 = cos_w * x_orb - sin_w * y_orb
    y1 = sin_w * x_orb + cos_w * y_orb
    x = cos_om * x1 - sin_om * y1 * cos_i
    y = sin_om * x1 + cos_om * y1 * cos_i
    z = y1 * sin_i
    return np.column_stack([x, y, z])


def earth_position(day: float) -> np.ndarray:
    """Approximate Earth as a circular 1 AU orbit."""
    theta = EARTH_MEAN_MOTION_RAD_PER_DAY * day
    return np.asarray([np.cos(theta), np.sin(theta), 0.0])


def solve_kepler(mean_anomaly: np.ndarray, eccentricity: np.ndarray) -> np.ndarray:
    """Solve Kepler's equation with vectorized Newton iterations."""
    mean_anomaly = np.mod(mean_anomaly, 2 * np.pi)
    eccentric_anomaly = mean_anomaly.copy()
    for _ in range(8):
        numerator = eccentric_anomaly - eccentricity * np.sin(eccentric_anomaly) - mean_anomaly
        denominator = 1 - eccentricity * np.cos(eccentric_anomaly)
        eccentric_anomaly = eccentric_anomaly - numerator / np.maximum(denominator, 1e-9)
    return eccentric_anomaly
