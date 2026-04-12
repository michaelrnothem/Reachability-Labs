import numpy as np

from reachability_labs_demo.gap_profile import compute_gap_profile


def test_gap_profile_nonnegative_when_existence_dominates():
    alpha = np.array([0.0, 1.0, 2.0, 3.0])
    existence = np.array([1.0, 0.8, 0.4, 0.0])
    reachability = np.array([1.0, 0.6, 0.2, 0.0])
    profile = compute_gap_profile(alpha, existence, reachability)
    assert np.all(profile.gap >= -1e-9)


def test_gap_profile_zero_when_curves_identical():
    alpha = np.array([0.0, 1.0, 2.0, 3.0])
    curve = np.array([1.0, 0.7, 0.3, 0.0])
    profile = compute_gap_profile(alpha, curve, curve)
    assert np.allclose(profile.gap, 0.0)


def test_midpoint_gap_matches_example_curve_expectation():
    alpha = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    existence = np.array([1.0, 0.95, 0.8, 0.35, 0.0])
    reachability = np.array([1.0, 0.5, 0.15, 0.0, 0.0])
    profile = compute_gap_profile(alpha, existence, reachability)
    assert profile.midpoint_gap > 0.0
