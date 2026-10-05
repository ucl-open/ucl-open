from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import swc.aeon.io.api as aeon
from dotmap import DotMap
from harp.io import MessageType, to_file
from swc.aeon.io import reader as aeon_reader
from swc.aeon.schema.streams import Device

from ucl_open.io import reader
from ucl_open.io.streams import csv, harp_device, raw_video

DEVICE_YML = """\
%YAML 1.1
---
device: TestDevice
whoAmI: 0
firmwareVersion: "0.1"
hardwareTargets: "0.1"
registers:
  AnalogData:
    address: 44
    type: S16
    length: 2
    access: Event
    payloadSpec:
      Channel0:
        offset: 0
      Channel1:
        offset: 1
  DigitalInputs:
    address: 45
    type: U8
    access: Event
    maskType: InputPins
bitMasks:
  InputPins:
    bits:
      DI0: 0x1
      DI1: 0x2
"""

SESSION = "ses-001_date-2026-10-03T16-14-20"
CHUNK_SECONDS = 36


def chunk_name(seconds: float) -> str:
    return aeon.to_datetime(seconds).strftime("%Y-%m-%dT%H-%M-%S")


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    """Generates a session with three 36-second chunks for each device."""
    session = tmp_path / "sub-Test" / SESSION
    harp_dir = session / "HarpDevice"
    video_dir = session / "Video"
    position_dir = session / "MousePosition"
    harp_dir.mkdir(parents=True)
    video_dir.mkdir(parents=True)
    position_dir.mkdir(parents=True)
    for chunk in range(3):
        start = chunk * CHUNK_SECONDS
        times = start + np.arange(0, CHUNK_SECONDS, 6.0)
        name = chunk_name(start)

        analog = pd.DataFrame({"a": np.arange(len(times)), "b": -np.arange(len(times))}, index=times)
        to_file(
            analog,
            harp_dir / f"HarpDevice_44_{name}.bin",
            address=44,
            dtype=np.dtype(np.int16),
            message_type=MessageType.EVENT,
        )
        digital = pd.DataFrame({"pins": np.arange(len(times)) % 4}, index=times)
        to_file(
            digital,
            harp_dir / f"HarpDevice_45_{name}.bin",
            address=45,
            dtype=np.dtype(np.uint8),
            message_type=MessageType.EVENT,
        )
        pd.DataFrame({"Seconds": times, "Value.Width": 640, "Value.Height": 480}).to_csv(
            video_dir / f"Video_{name}.csv", index=False
        )
        pd.DataFrame({"Seconds": times, "Value.X": times * 2, "Value.Y": times * 3}).to_csv(
            position_dir / f"MousePosition_{name}.csv", index=False
        )

    (tmp_path / "device.yml").write_text(DEVICE_YML)
    return session


@pytest.fixture
def experiment(dataset: Path) -> DotMap:
    return DotMap(
        [
            Device("HarpDevice", harp_device(dataset.parents[1] / "device.yml")),
            Device("MousePosition", csv(columns=("x", "y"))),
            Device("Video", raw_video()),
        ]
    )


def test_csv_creates_singleton_reader(experiment: DotMap):
    assert isinstance(experiment.MousePosition, aeon_reader.Csv)
    assert experiment.MousePosition.pattern == "MousePosition_*"
    assert experiment.MousePosition.extension == "csv"


def test_load_csv(dataset: Path, experiment: DotMap):
    data = aeon.load(dataset, experiment.MousePosition)
    assert list(data.columns) == ["x", "y"]
    assert len(data) == 18
    assert data.index.is_monotonic_increasing
    assert data.x.iloc[-1] == 204.0


def test_raw_video_creates_singleton_reader(experiment: DotMap):
    assert isinstance(experiment.Video, reader.RawVideo)
    assert experiment.Video.pattern == "Video_*"
    assert experiment.Video.video_extension == "avi"


def test_harp_device_creates_register_readers(experiment: DotMap):
    registers = experiment.HarpDevice
    assert isinstance(registers.AnalogData, reader.Harp)
    assert registers.AnalogData.pattern == "HarpDevice_44_*"
    assert registers.AnalogData.extension == "bin"
    assert list(registers.AnalogData.columns) == ["Channel0", "Channel1"]


def test_load_harp_payload_spec(dataset: Path, experiment: DotMap):
    data = aeon.load(dataset, experiment.HarpDevice.AnalogData)
    assert list(data.columns) == ["Channel0", "Channel1"]
    assert len(data) == 18
    assert data.index.is_monotonic_increasing
    assert data.index[-1] == aeon.to_datetime(102.0)


def test_load_harp_bitmask(dataset: Path, experiment: DotMap):
    data = aeon.load(dataset, experiment.HarpDevice.DigitalInputs)
    assert list(data.columns) == ["DI0", "DI1"]
    assert data.dtypes.eq(bool).all()
    assert list(data.DI0[:4]) == [False, True, False, True]
    assert list(data.DI1[:4]) == [False, False, True, True]


def test_load_harp_time_range(dataset: Path, experiment: DotMap):
    start = aeon.to_datetime(30.0)
    end = aeon.to_datetime(48.0)
    data = aeon.load(dataset, experiment.HarpDevice.AnalogData, start=start, end=end)
    assert list(aeon.to_seconds(data.index)) == [30.0, 36.0, 42.0, 48.0]


def test_load_raw_video(dataset: Path, experiment: DotMap):
    data = aeon.load(dataset, experiment.Video)
    assert list(data.columns) == ["width", "height", "_frame", "_path", "_epoch"]
    assert len(data) == 18
    first, last = data.iloc[0], data.iloc[-1]
    assert first["width"] == 640
    assert first["height"] == 480
    assert first["_frame"] == 0
    assert last["_frame"] == 5
    assert first["_path"].endswith(f"Video_{chunk_name(0)}.avi")
    assert last["_path"].endswith(f"Video_{chunk_name(72)}.avi")
    assert first["_epoch"] == SESSION


def test_load_missing_harp_register_is_empty(tmp_path: Path, experiment: DotMap):
    data = aeon.load(tmp_path / "missing", experiment.HarpDevice.AnalogData)
    assert data.empty
    assert list(data.columns) == ["Channel0", "Channel1"]
