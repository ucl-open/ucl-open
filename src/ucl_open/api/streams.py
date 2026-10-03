"""Stream factories for declaring the devices in a ucl-open dataset.

Each factory is passed to an `swc.aeon.schema.streams.Device`, which calls it with
the device directory name to create the readers for each data stream.
"""

from collections.abc import Callable
from os import PathLike

import harp
from harp.model import Model
from pandas._typing import DtypeArg, SequenceNotStr
from swc.aeon.io.api import Reader

from ucl_open.api import reader as _reader

StreamFactory = Callable[[str], dict[str, Reader]]


def csv_reader(columns: SequenceNotStr[str] = (), dtype: DtypeArg | None = None) -> StreamFactory:
    """Declares a single-stream device logged as CSV files.

    Args:
        columns: Optional column labels for the data. If not specified, the file header is used.
        dtype: Optional data type for the data columns.
    """
    return lambda path: {path: _reader.Csv(f"{path}_*", columns, dtype)}


def video_reader(video_extension: str = "avi") -> StreamFactory:
    """Declares a video device, reading the frame metadata stored alongside each video file.

    Args:
        video_extension: The file extension of the video files.
    """
    return lambda path: {path: _reader.Video(f"{path}_*", video_extension)}


def harp_reader(device: str | PathLike | Model, include_common_registers: bool = True) -> StreamFactory:
    """Declares a Harp device, with one data stream per device register.

    Args:
        device: Path to the device schema (`device.yml`) or a parsed device schema.
        include_common_registers: Specifies whether to include the Harp common registers.
    """
    device_reader = harp.create_reader(device, include_common_registers=include_common_registers)
    return lambda path: _reader.create_harp_registers(path, device_reader)
