"""Readers for extracting data from raw files in a ucl-open dataset."""

from pathlib import Path

import harp
import pandas as pd
from harp.reader import RegisterReader
from pandas._typing import DtypeArg, SequenceNotStr
from swc.aeon.io.api import Reader


class Csv(Reader):
    """Extracts data from comma-separated (CSV) text files.

    The first column stores the `Seconds` timestamp. If no column labels are
    specified, the labels in the file header are used.
    """

    def __init__(
        self,
        pattern: str,
        columns: SequenceNotStr[str] = (),
        dtype: DtypeArg | None = None,
        extension="csv",
    ):
        """Initialize the object with the specified pattern, columns, and data type."""
        super().__init__(pattern, columns, extension)
        self.dtype = dtype

    def read(self, path: Path) -> pd.DataFrame:
        """Reads data from the specified CSV text file.

        Args:
            path: Path to the CSV text file.

        Returns:
            A DataFrame representing the data extracted from the CSV text file,
            indexed by the timestamp in the first column.
        """
        if path.stat().st_size == 0:
            return pd.DataFrame(columns=self.columns, index=pd.Index([], dtype=float))
        names = ("Seconds", *self.columns) if self.columns else None
        return pd.read_csv(path, header=0, names=names, dtype=self.dtype, index_col=0)


class Video(Csv):
    """Extracts video frame metadata.

    Columns are read from the frame metadata file header, with the additional columns:

    - _frame (int): Frame index in the video file.
    - _path (str): Path to the video file.
    - _epoch (str): Session directory associated with the video file.
    """

    def __init__(self, pattern: str, video_extension: str = "avi"):
        """Initialize the object with a specified pattern and video file extension."""
        super().__init__(pattern)
        self.video_extension = video_extension

    def read(self, path: Path) -> pd.DataFrame:
        """Reads video frame metadata from the specified file.

        Args:
            path: Path to the video frame metadata CSV file.

        Returns:
            A DataFrame containing the video frame metadata.
        """
        data = super().read(path)
        data["_frame"] = range(len(data))
        data["_path"] = str(path.with_suffix(f".{self.video_extension}"))
        data["_epoch"] = path.parts[-3]
        return data


class HarpRegister(Reader):
    """Extracts data for a single register from Harp binary files.

    Register payloads are decoded according to the device schema, using
    the register reader created by `harp.create_reader`.
    """

    def __init__(self, pattern: str, register: RegisterReader, extension="bin"):
        """Initialize the object with the specified pattern and register reader."""
        self.register = register
        super().__init__(pattern, self._columns(register), extension)

    @staticmethod
    def _columns(register: RegisterReader) -> list[str]:
        try:
            return list(register.read(b"").columns)
        except Exception:
            return []

    def read(self, path: Path) -> pd.DataFrame:
        """Reads data from the specified Harp binary file.

        Args:
            path: Path to the Harp binary file.

        Returns:
            A DataFrame representing the decoded register data.
        """
        return self.register.read(path)


def create_harp_registers(path: str, device: harp.reader.DeviceReader) -> dict[str, HarpRegister]:
    """Creates a reader for every register in a Harp device.

    Args:
        path: The device name prefix of the register files.
        device: The device reader created from the device schema.

    Returns:
        A dictionary mapping register names to register readers.
    """
    return {
        name: HarpRegister(f"{path}_{register.register.address}_*", register)
        for name, register in device.registers.items()
    }
