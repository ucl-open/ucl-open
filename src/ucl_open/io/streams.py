"""Stream factories for declaring ucl-open devices with `swc.aeon.schema.streams.Device`."""

from collections.abc import Callable
from os import PathLike

import harp
from harp.model import Model
from pandas._typing import DtypeArg, SequenceNotStr
from swc.aeon.io import reader as _aeon_reader

from ucl_open.io import reader as _reader


def csv(
    columns: SequenceNotStr[str], dtype: DtypeArg | None = None
) -> Callable[[str], dict[str, _aeon_reader.Csv]]:
    """Declares a single-stream device logged as CSV files.

    The returned factory creates an `swc.aeon.io.reader.Csv` reader matching files
    named `<Device>_<DateTime>.csv`. The first column of each file (`Seconds`) is
    used as the time index.

    Args:
        columns: Column labels for the data, excluding the `Seconds` timestamp column.
        dtype: Optional data type for the data columns.

    Returns:
        A stream factory to pass to `swc.aeon.schema.streams.Device`.

    Examples:
        >>> experiment = DotMap([Device("MousePosition", csv(columns=("x", "y", "z")))])
        >>> api.load(root, experiment.MousePosition)
    """

    def streams(path: str) -> dict[str, _aeon_reader.Csv]:
        return {path: _aeon_reader.Csv(f"{path}_*", columns, dtype)}

    return streams


def raw_video(video_extension: str = "avi") -> Callable[[str], dict[str, _reader.RawVideo]]:
    """Declares a video device logged with `LogRawVideo`.

    The returned factory creates a `RawVideo` reader matching the frame metadata
    files named `<Device>_<DateTime>.csv` stored alongside each video file.

    Args:
        video_extension: The file extension of the video files.

    Returns:
        A stream factory to pass to `swc.aeon.schema.streams.Device`.

    Examples:
        >>> experiment = DotMap([Device("Video", raw_video())])
        >>> api.load(root, experiment.Video)
    """

    def streams(path: str) -> dict[str, _reader.RawVideo]:
        return {path: _reader.RawVideo(f"{path}_*", video_extension)}

    return streams


def harp_device(
    device: str | PathLike | Model, include_common_registers: bool = True
) -> Callable[[str], dict[str, _reader.Harp]]:
    """Declares a Harp device logged with one file per register.

    The returned factory creates a `Harp` reader for every register in the
    device schema, matching files named `<Device>_<Address>_<DateTime>.bin`.

    Args:
        device: Path to the device schema (`device.yml`), or a parsed device schema.
        include_common_registers: Specifies whether to include the Harp common registers.

    Returns:
        A stream factory to pass to `swc.aeon.schema.streams.Device`.

    Examples:
        >>> experiment = DotMap([Device("Behavior", harp_device("device.yml"))])
        >>> api.load(root, experiment.Behavior.DigitalInputState)
    """
    device_reader = harp.create_reader(device, include_common_registers=include_common_registers)

    def streams(path: str) -> dict[str, _reader.Harp]:
        return {
            name: _reader.Harp(f"{path}_{register.register.address}_*", device_reader, name)
            for name, register in device_reader.registers.items()
        }

    return streams
