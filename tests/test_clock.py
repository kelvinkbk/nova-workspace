from core.clock import calculate_life_day


def test_life_day_calculation():
    assert calculate_life_day("2026-01-01T00:00:00+00:00") >= 1
