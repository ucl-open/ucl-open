import numpy as np
import pandas as pd
import pytest
import swc.aeon.io.api as aeon

from ucl_open.io.sync import synchronise_to

SLOPE = 1.1
OFFSET = 3.5


def other_clock(seconds):
    return SLOPE * np.asarray(seconds) + OFFSET


@pytest.fixture
def data() -> pd.DataFrame:
    seconds = np.arange(0.0, 100.0, 7.0)
    return pd.DataFrame(
        {"value": np.arange(len(seconds))}, index=aeon.to_datetime(pd.Index(seconds, name="time"))
    )


def test_synchronise_datetime_index(data: pd.DataFrame):
    from_clock = aeon.to_datetime(pd.Index([0.0, 50.0, 120.0]))
    to_clock = aeon.to_datetime(pd.Index(other_clock([0.0, 50.0, 120.0])))
    result = synchronise_to(data, from_clock, to_clock)

    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.name == "time"
    expected = other_clock(aeon.to_seconds(data.index))
    np.testing.assert_allclose(aeon.to_seconds(result.index), expected, atol=1e-6)
    pd.testing.assert_series_equal(result.value.reset_index(drop=True), data.value.reset_index(drop=True))


def test_synchronise_mixed_clock_types(data: pd.DataFrame):
    """Clocks can be datetimes or Harp seconds, e.g. a pulse logged as a value."""
    pulses = pd.Series(other_clock([10.0, 60.0]), index=aeon.to_datetime(pd.Index([10.0, 60.0])))
    result = synchronise_to(data, from_clock=pulses.index, to_clock=pulses)
    np.testing.assert_allclose(
        aeon.to_seconds(result.index), other_clock(aeon.to_seconds(data.index)), atol=1e-6
    )


def test_synchronise_inverse_mapping(data: pd.DataFrame):
    pulses = pd.Series(other_clock([10.0, 60.0]), index=aeon.to_datetime(pd.Index([10.0, 60.0])))
    remapped = synchronise_to(data, from_clock=pulses.index, to_clock=pulses)
    restored = synchronise_to(remapped, from_clock=pulses, to_clock=pulses.index)
    np.testing.assert_allclose(aeon.to_seconds(restored.index), aeon.to_seconds(data.index), atol=1e-6)


def test_synchronise_seconds_index():
    data = pd.DataFrame({"value": [1, 2, 3]}, index=pd.Index([1.0, 2.0, 3.0], name="Seconds"))
    result = synchronise_to(data, [0.0, 10.0], other_clock([0.0, 10.0]))
    assert not isinstance(result.index, pd.DatetimeIndex)
    assert result.index.name == "Seconds"
    np.testing.assert_allclose(result.index, other_clock([1.0, 2.0, 3.0]))


def test_synchronise_large_clock_values():
    """Precision is preserved for timestamps far from the clock epoch."""
    start = 3.9e9
    data = pd.DataFrame({"value": [0, 1]}, index=pd.Index([start + 1.0, start + 1.001]))
    sync = start + np.array([0.0, 100.0, 200.0])
    result = synchronise_to(data, sync, sync + 0.25)
    np.testing.assert_allclose(result.index - start, [1.25, 1.251], atol=1e-6)


def test_synchronise_least_squares_fit(data: pd.DataFrame):
    rng = np.random.default_rng(0)
    sync = np.linspace(0.0, 100.0, 50)
    to_clock = other_clock(sync) + rng.normal(0, 0.001, len(sync))
    result = synchronise_to(data, sync, to_clock)
    np.testing.assert_allclose(
        aeon.to_seconds(result.index), other_clock(aeon.to_seconds(data.index)), atol=0.005
    )


def test_synchronise_ignores_missing_pairs(data: pd.DataFrame):
    result = synchronise_to(data, [0.0, np.nan, 50.0], [OFFSET, 1.0, float(other_clock(50.0))])
    np.testing.assert_allclose(
        aeon.to_seconds(result.index), other_clock(aeon.to_seconds(data.index)), atol=1e-6
    )


def test_synchronise_does_not_modify_input(data: pd.DataFrame):
    original = data.copy()
    synchronise_to(data, [0.0, 10.0], other_clock([0.0, 10.0]))
    pd.testing.assert_frame_equal(data, original)


def test_synchronise_length_mismatch(data: pd.DataFrame):
    with pytest.raises(ValueError, match="same length"):
        synchronise_to(data, [0.0, 1.0, 2.0], [0.0, 1.0])


def test_synchronise_requires_two_timestamps(data: pd.DataFrame):
    with pytest.raises(ValueError, match="two distinct"):
        synchronise_to(data, [5.0, 5.0], [1.0, 2.0])
