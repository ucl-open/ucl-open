"""Utilities for synchronising data recorded on different clocks."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from swc.aeon.io.api import to_datetime, to_seconds

ClockTimes = pd.Index | pd.Series | np.ndarray | Sequence[float]


def _seconds(times: ClockTimes) -> np.ndarray:
    """Converts datetime or Harp seconds timestamps to an array of Harp seconds."""
    if isinstance(times, pd.Series | pd.Index):
        values = times
    else:
        values = pd.Index(np.asarray(times))
    if pd.api.types.is_datetime64_any_dtype(values):
        values = to_seconds(pd.DatetimeIndex(values))
    return np.asarray(values, dtype=np.float64)


def synchronise_to(data: pd.DataFrame, from_clock: ClockTimes, to_clock: ClockTimes) -> pd.DataFrame:
    """Remaps the time index of data from one clock to another.

    A linear mapping from `from_clock` to `to_clock` is fitted by least squares to
    the pairs of corresponding timestamps, and applied to the time index of `data`.
    Timestamps can be given as datetimes or as Harp seconds, in any combination.

    Args:
        data: The data to synchronise, indexed by time on the same clock as `from_clock`.
        from_clock: Timestamps of synchronisation events on the clock of `data`.
        to_clock: Timestamps of the same synchronisation events on the target clock.

    Returns:
        A copy of `data` with the time index remapped to the target clock. The index
        has the same type as the index of `data`.

    Examples:
        Map video data onto the clock of a device receiving pulses logged from the video clock:

        >>> synchronise_to(video, from_clock=async_pulse.pulse, to_clock=async_pulse.index)
    """
    source = _seconds(from_clock)
    target = _seconds(to_clock)
    if len(source) != len(target):
        raise ValueError(
            f"from_clock and to_clock must have the same length, but got {len(source)} and {len(target)}."
        )

    valid = np.isfinite(source) & np.isfinite(target)
    source, target = source[valid], target[valid]
    if len(np.unique(source)) < 2:
        raise ValueError("At least two distinct synchronisation timestamps are required.")

    # Center timestamps before fitting to preserve precision for large clock values
    source_offset, target_offset = source.mean(), target.mean()
    slope, intercept = np.polyfit(source - source_offset, target - target_offset, 1)

    index = data.index
    seconds = _seconds(index)
    remapped = slope * (seconds - source_offset) + intercept + target_offset
    result = data.copy()
    if isinstance(index, pd.DatetimeIndex):
        result.index = pd.DatetimeIndex(to_datetime(pd.Index(remapped)), name=index.name)
    else:
        result.index = pd.Index(remapped, name=index.name)
    return result
