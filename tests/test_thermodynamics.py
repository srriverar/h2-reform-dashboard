import numpy as np

from core.metrics import calculate_metrics
from core.thermodynamics import ELEMENT_MATRIX, build_feed, solve_equilibrium


def test_smr_conserves_elements():
    result = solve_equilibrium("SMR", 850.0, 3.0, 3.0)
    assert result.success
    np.testing.assert_allclose(
        ELEMENT_MATRIX @ result.feed,
        ELEMENT_MATRIX @ result.outlet,
        atol=1e-7,
    )


def test_hotter_smr_has_higher_conversion_in_screening_range():
    low = solve_equilibrium("SMR", 550.0, 1.0, 3.0)
    high = solve_equilibrium("SMR", 900.0, 1.0, 3.0)
    x_low = 100 * (1 - low.outlet[0] / low.feed[0])
    x_high = 100 * (1 - high.outlet[0] / high.feed[0])
    assert x_high > x_low


def test_metrics_are_finite_for_all_routes():
    ratios = {"SMR": 3.0, "DRM": 1.0, "POX": 0.5}
    for route, ratio in ratios.items():
        result = solve_equilibrium(route, 850.0, 5.0, ratio)
        metrics = calculate_metrics(result)
        assert result.success
        assert all(np.isfinite(value) for value in metrics.values())
        assert 0 <= metrics["Conversión CH4 (%)"] <= 100


def test_feed_definitions():
    smr = build_feed("SMR", 3.0)
    drm = build_feed("DRM", 1.0)
    pox = build_feed("POX", 0.5)
    assert tuple(smr[[0, 1]]) == (1.0, 3.0)
    assert tuple(drm[[0, 3]]) == (1.0, 1.0)
    assert tuple(pox[[0, 5]]) == (1.0, 0.5)
