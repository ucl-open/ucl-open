"""Readers for extracting data from raw files in a ucl-open dataset.

These readers extend `swc.aeon.io.reader` and are used with `swc.aeon.io.api.load`.
"""

from pathlib import Path

import pandas as pd
from harp.model import Model
from harp.reader import DeviceReader, RegisterReader
from swc.aeon.io.reader import Reader


def _register_columns(device: Model, name: str) -> list[str]:
    """Returns the column labels produced by harp-python when decoding the specified register."""
    register = device.registers[name]
    if register.maskType is not None:
        key = register.maskType.root
        if device.bitMasks is not None and key in device.bitMasks:
            return list(device.bitMasks[key].bits.keys())
        if device.groupMasks is not None and key in device.groupMasks:
            return [name]
    if register.payloadSpec is not None:
        return list(register.payloadSpec.keys())
    if register.length is None or register.length == 1:
        return [name]
    return [f"{name}_{i}" for i in range(register.length)]


class Harp(Reader):
    """Extracts data from a single Harp register, decoded using the device schema.

    Unlike `swc.aeon.io.reader.Harp`, register payloads are decoded with the
    register reader created by `harp.create_reader`, so columns, bit masks and
    payload members follow the device schema (`device.yml`).
    """

    register: RegisterReader
    """The harp-python reader used to decode the register."""

    def __init__(self, pattern: str, device: DeviceReader, register: str, extension: str = "bin"):
        """Initialize the object with the specified pattern and device register.

        Args:
            pattern: Pattern used to find raw files, usually in the format `<Device>_<Address>_*`.
            device: The harp-python device reader, created with `harp.create_reader`.
            register: The name of the register to read.
            extension: Extension of data file pathnames.
        """
        self.register = device.registers[register]
        super().__init__(pattern, columns=_register_columns(device.device, register), extension=extension)

    def read(self, path: Path) -> pd.DataFrame:
        """Reads data from the specified Harp binary file.

        Args:
            path: Path to the Harp binary file.

        Returns:
            A DataFrame representing the decoded register data.
        """
        return self.register.read(path)


class RawVideo(Reader):
    """Extracts video frame metadata for videos logged without camera metadata.

    Columns:

    - width (int): Width of the video frame, in pixels.
    - height (int): Height of the video frame, in pixels.
    - _frame (int): Frame index in the video file.
    - _path (str): Path to the video file.
    - _epoch (str): Session directory associated with the video file.
    """

    def __init__(self, pattern: str, video_extension: str = "avi"):
        """Initialize the object with a specified pattern and video file extension."""
        super().__init__(pattern, columns=("width", "height", "_frame", "_path", "_epoch"), extension="csv")
        self.video_extension = video_extension
        self._rawcolumns = ("time",) + tuple(self.columns[0:2])

    def read(self, path: Path) -> pd.DataFrame:
        """Reads video frame metadata from the specified file.

        Args:
            path: Path to the video frame metadata CSV file.

        Returns:
            A DataFrame containing the video frame metadata.
        """
        data = pd.read_csv(path, header=0, names=self._rawcolumns)
        data["_frame"] = data.index
        data["_path"] = str(path.with_suffix(f".{self.video_extension}"))
        data["_epoch"] = path.parts[-3]
        data.set_index("time", inplace=True)
        return data
